"""
Badges endpoints: CRUD and suggested thresholds:
    - Reading badges recalculates them first: avoid badges grow with time, without new sessions
    - Consistency and streak badges come with their progress in the current period
"""

# Imports
import datetime as dt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import current_user, find_in_habit, owned_badge, owned_habit, user_today
from app.enums import TagRule
from app.models import Badge, BadgeTag, Habit, Metric, Tag, User
from app.schemas import BadgeCreate, BadgeOut, BadgeUpdate, TiersOut
from app.services.badges import badge_progress, recalculate_badges
from app.services.history import load_history
from app.services.tiers import suggest_tiers

router = APIRouter()


@router.get("/badges", status_code=200, response_model=list[BadgeOut])
def list_badges(user: User = Depends(current_user), today: dt.date = Depends(user_today), db: Session = Depends(get_db)):
    """Every badge of the user, habit by habit, for the badges view."""
    habits = db.scalars(select(Habit).where(Habit.user_id == user.id).order_by(Habit.created_at)).all()
    badges = [badge for habit in habits for badge in fresh_badges(db, habit, today)]

    db.commit()
    return badges


@router.get("/badges/suggest-tiers", status_code=200, response_model=TiersOut)
def get_suggested_tiers(first: float, diamond: float, user: User = Depends(current_user)):
    """Suggested thresholds from the first one to diamond, to review before saving the badge."""
    try:
        return TiersOut(tiers=suggest_tiers(first, diamond))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))


@router.get("/habits/{habit_id}/badges", status_code=200, response_model=list[BadgeOut])
def list_habit_badges(habit: Habit = Depends(owned_habit), today: dt.date = Depends(user_today),
                      db: Session = Depends(get_db)):
    """Every badge of a habit."""
    badges = fresh_badges(db, habit, today)

    db.commit()
    return badges


@router.get("/badges/{badge_id}", status_code=200, response_model=BadgeOut)
def get_badge(badge: Badge = Depends(owned_badge), today: dt.date = Depends(user_today), db: Session = Depends(get_db)):
    """One badge."""
    return save_and_show(db, badge, today)


@router.post("/habits/{habit_id}/badges", status_code=201, response_model=BadgeOut)
def create_badge(data: BadgeCreate, habit: Habit = Depends(owned_habit), today: dt.date = Depends(user_today),
                 db: Session = Depends(get_db)):
    """Creates a badge; it takes the habit's history at once and starts at the tier it has earned."""
    if data.metric_id is not None:
        find_in_habit(db, Metric, [data.metric_id], habit)

    # Create
    badge = Badge(
        habit_id=habit.id,
        metric_id=data.metric_id,
        name=data.name,
        kind=data.kind,
        higher_is_better=data.higher_is_better,
        threshold=data.threshold,
        period=data.period,
        target=data.target,
        mode=data.mode,
        untagged_only=data.untagged_only,
        tag_rules=tag_rules(db, habit, data.required_tag_ids, data.excluded_tag_ids),
        unlocked=data.unlocked,
        bronze=data.bronze,
        silver=data.silver,
        gold=data.gold,
        diamond=data.diamond,
    )
    db.add(badge)

    return save_and_show(db, badge, today)


@router.patch("/badges/{badge_id}", status_code=200, response_model=BadgeOut)
def update_badge(data: BadgeUpdate, badge: Badge = Depends(owned_badge), today: dt.date = Depends(user_today),
                 db: Session = Depends(get_db)):
    """Partial update, checked as a whole badge; its kind and metric are fixed."""
    habit = db.get(Habit, badge.habit_id)
    changes = data.model_dump(exclude_unset=True)
    merged = check_merged(badge, changes)

    # Update
    for field, value in changes.items():
        if field not in ("required_tag_ids", "excluded_tag_ids"):
            setattr(badge, field, value)

    if changes.keys() & {"required_tag_ids", "excluded_tag_ids"}:
        badge.tag_rules = tag_rules(db, habit, merged.required_tag_ids, merged.excluded_tag_ids)

    return save_and_show(db, badge, today)


@router.delete("/badges/{badge_id}", status_code=204)
def delete_badge(badge: Badge = Depends(owned_badge), db: Session = Depends(get_db)):
    """Deletes a badge; nothing else goes with it."""
    db.delete(badge)
    db.commit()


def fresh_badges(db: Session, habit: Habit, today: dt.date) -> list[BadgeOut]:
    """Badges of a habit, recalculated for today and with their progress; the caller commits."""
    history = load_history(db, habit.id)
    recalculate_badges(db, habit, today, history)

    badges = db.scalars(select(Badge).where(Badge.habit_id == habit.id).order_by(Badge.created_at))
    return [badge_out(badge, history, habit, today) for badge in badges]


def save_and_show(db: Session, badge: Badge, today: dt.date) -> BadgeOut:
    """One badge recalculated with its habit, saved, and returned with its progress."""
    db.flush()
    habit = db.get(Habit, badge.habit_id)
    history = load_history(db, habit.id)
    recalculate_badges(db, habit, today, history)

    response = badge_out(badge, history, habit, today)
    db.commit()
    return response


def badge_out(badge: Badge, history: list, habit: Habit, today: dt.date) -> BadgeOut:
    """Badge row → response, with its progress in the current period."""
    progress = badge_progress(badge, history, habit.start_date, today)
    return BadgeOut.model_validate(badge).model_copy(update={"progress": progress})


def tag_rules(db: Session, habit: Habit, required_ids: list, excluded_ids: list) -> list[BadgeTag]:
    """Tag filters of a badge, with tags of the same habit (404 / 400)."""
    required = find_in_habit(db, Tag, required_ids, habit)
    excluded = find_in_habit(db, Tag, excluded_ids, habit)

    return ([BadgeTag(tag_id=tag.id, rule=TagRule.REQUIRED) for tag in required]
            + [BadgeTag(tag_id=tag.id, rule=TagRule.EXCLUDED) for tag in excluded])


def check_merged(badge: Badge, changes: dict) -> BadgeCreate:
    """The badge as it would end up, checked with the same rules as a new one → 422 if it breaks one."""
    current = {field: getattr(badge, field) for field in BadgeCreate.model_fields if hasattr(badge, field)}
    current["required_tag_ids"] = [rule.tag_id for rule in badge.tag_rules if rule.rule == TagRule.REQUIRED]
    current["excluded_tag_ids"] = [rule.tag_id for rule in badge.tag_rules if rule.rule == TagRule.EXCLUDED]

    try:
        return BadgeCreate.model_validate(current | changes)
    except ValidationError as error:
        raise RequestValidationError(error.errors())
