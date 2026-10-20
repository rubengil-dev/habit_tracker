"""
Badges endpoints: CRUD, with badges recalculation on create and update.
"""

# Imports
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Badges, Habits, Metrics
from schemas import BadgeCreate, BadgeUpdate, BadgeResponse
from services.badge_progress import recalculate_badges
from services.calc_streaks import current_badge_progress

router = APIRouter()


def build_badge_response(badge: Badges, db: Session, with_progress: bool = False) -> BadgeResponse:
    """
    Badge response builder:
        - Adds current_progress only if requested and only for consistency badges
    """

    response = BadgeResponse.model_validate(badge)

    if with_progress and badge.metric_type == "consistency":
        response.current_progress = current_badge_progress(badge, db)

    return response


@router.get("/badges", status_code=200, response_model=list[BadgeResponse])
def list_badges(db: Session = Depends(get_db)):
    """Returns every badge."""

    # Query
    badges = db.query(Badges).all()
    return [build_badge_response(b, db, with_progress=True) for b in badges]


@router.get("/habits/{habit_id}/badges", status_code=200, response_model=list[BadgeResponse])
def list_badges_related(habit_id: int, db: Session = Depends(get_db)):
    """Returns every badge of a habit."""

    # Habit check
    habit = db.query(Habits).filter(Habits.id == habit_id).first()

    if habit is None:
        raise HTTPException(status_code=404, detail=f"Habit #{habit_id} not found")

    # Query
    badges = db.query(Badges).filter(Badges.habit_id == habit_id).all()
    return [build_badge_response(b, db, with_progress=True) for b in badges]


@router.get("/badges/{id}", status_code=200, response_model=BadgeResponse)
def get_badge(id: int, db: Session = Depends(get_db)):
    """Returns one badge."""

    # Query
    badge = db.query(Badges).filter(Badges.id == id).first()

    # Existence check
    if badge is None:
        raise HTTPException(status_code=404, detail="Badge not found")
    return build_badge_response(badge, db, with_progress=True)


@router.post("/badges", status_code=201, response_model=BadgeResponse)
def create_badge(data: BadgeCreate, db: Session = Depends(get_db)):
    """Creates a badge → recalculates its tier."""

    # Habit check
    habit = db.query(Habits).filter(Habits.id == data.habit_id).first()

    if habit is None:
        raise HTTPException(status_code=404, detail=f"Habit #{data.habit_id} not found")

    # Metric check
    metric = db.query(Metrics).filter(Metrics.id == data.metric_id).first()

    if metric is None:
        raise HTTPException(status_code=404, detail=f"Metric #{data.metric_id} not found")

    # Ownership check
    if metric.habit_id != data.habit_id:
        raise HTTPException(status_code=400, detail="metric_id does not belong to habit_id")

    # Create
    new_badge = Badges(
        habit_id=data.habit_id,
        metric_id=data.metric_id,
        badge=data.badge,
        metric_type=data.metric_type,
        unlocked=data.unlocked,
        bronze=data.bronze,
        silver=data.silver,
        gold=data.gold,
        diamond=data.diamond,
        frequency_target=data.frequency_target,
        frequency_period=data.frequency_period,
        higher_is_better=data.higher_is_better,
        threshold_value=data.threshold_value
    )

    # Save
    db.add(new_badge)
    db.commit()
    db.refresh(new_badge)

    # Recalculation: commits inside, so the badge is refreshed again
    recalculate_badges(db, new_badge.metric_id)
    db.refresh(new_badge)

    # Progress is for display only, so it is not computed here
    return build_badge_response(new_badge, db, with_progress=False)


@router.patch("/badges/{id}", status_code=200, response_model=BadgeResponse)
def update_badge(id: int, data: BadgeUpdate, db: Session = Depends(get_db)):
    """Updates a badge → recalculates its tier."""

    # Query
    badge = db.query(Badges).filter(Badges.id == id).first()

    # Existence check
    if badge is None:
        raise HTTPException(status_code=404, detail="Badge not found")

    # Final foreign keys
    update_data = data.model_dump(exclude_unset=True)
    new_habit_id = update_data.get("habit_id", badge.habit_id)
    new_metric_id = update_data.get("metric_id", badge.metric_id)

    # Habit check
    if "habit_id" in update_data:
        habit = db.query(Habits).filter(Habits.id == new_habit_id).first()

        if habit is None:
            raise HTTPException(status_code=404, detail=f"Habit #{new_habit_id} not found")

    # Metric check
    if "metric_id" in update_data:
        metric = db.query(Metrics).filter(Metrics.id == new_metric_id).first()

        if metric is None:
            raise HTTPException(status_code=404, detail=f"Metric #{new_metric_id} not found")

    # Ownership check
    if "habit_id" in update_data or "metric_id" in update_data:
        metric = db.query(Metrics).filter(Metrics.id == new_metric_id).first()

        if metric.habit_id != new_habit_id:
            raise HTTPException(status_code=400, detail="metric_id does not belong to habit_id")

    # Previous metric
    old_metric_id = badge.metric_id

    # Update
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(badge, key, value)

    # Save
    db.commit()
    db.refresh(badge)

    # Recalculation: old and new metric
    metric_ids = {old_metric_id, badge.metric_id}
    for metric_id in metric_ids:
        recalculate_badges(db, metric_id)

    db.refresh(badge)

    # Progress is for display only, so it is not computed here
    return build_badge_response(badge, db, with_progress=False)


@router.delete("/badges/{id}", status_code=204)
def delete_badge(id: int, db: Session = Depends(get_db)):
    """Deletes a badge."""

    # Query
    badge = db.query(Badges).filter(Badges.id == id).first()

    # Existence check
    if badge is None:
        raise HTTPException(status_code=404, detail="Badge not found")

    # Save
    db.delete(badge)
    db.commit()
