"""
Sessions endpoints: CRUD; every write answers with the badges it changed and the habit's streaks.
"""

# Imports
import datetime as dt
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import find_in_habit, owned_entry, owned_habit, user_today
from app.enums import MetricKind
from app.models import Entry, EntryValue, Habit, Metric, Tag
from app.schemas import BadgeChangeOut, EffectsOut, EntryCreate, EntryOut, EntryUpdate, EntryWriteOut
from app.services.badges import recalculate_badges
from app.services.history import load_history
from app.services.ratios import refresh_ratios
from app.services.streaks import habit_streaks

router = APIRouter()


@router.get("/habits/{habit_id}/entries", status_code=200, response_model=list[EntryOut])
def list_entries(start: dt.date | None = None, end: dt.date | None = None,
                 habit: Habit = Depends(owned_habit), db: Session = Depends(get_db)):
    """Sessions of a habit, newest first; optionally only between two dates, both included."""
    query = select(Entry).where(Entry.habit_id == habit.id)

    if start is not None:
        query = query.where(Entry.date >= start)
    if end is not None:
        query = query.where(Entry.date <= end)

    return db.scalars(query.order_by(Entry.date.desc(), Entry.created_at.desc())).all()


@router.get("/entries/{entry_id}", status_code=200, response_model=EntryOut)
def get_entry(entry: Entry = Depends(owned_entry)):
    """One session."""
    return entry


@router.post("/habits/{habit_id}/entries", status_code=201, response_model=EntryWriteOut)
def create_entry(data: EntryCreate, habit: Habit = Depends(owned_habit), today: dt.date = Depends(user_today),
                 db: Session = Depends(get_db)):
    """Logs a session, today unless another date is given → the session, badge changes and streaks."""
    entry_date = data.date or today
    check_date(entry_date, habit, today)

    # Create
    entry = Entry(habit_id=habit.id, date=entry_date)
    set_values(db, entry, habit, data.values)
    entry.tags = find_in_habit(db, Tag, data.tag_ids, habit)
    db.add(entry)

    return save_and_report(db, habit, today, entry)


@router.patch("/entries/{entry_id}", status_code=200, response_model=EntryWriteOut)
def update_entry(data: EntryUpdate, entry: Entry = Depends(owned_entry), today: dt.date = Depends(user_today),
                 db: Session = Depends(get_db)):
    """Changes the date, values or tags of a session; values and tags sent replace the old ones."""
    habit = db.get(Habit, entry.habit_id)
    changes = data.model_dump(exclude_unset=True)

    # Update
    if "date" in changes:
        check_date(changes["date"], habit, today)
        entry.date = changes["date"]
    if "values" in changes:
        set_values(db, entry, habit, changes["values"])
    if "tag_ids" in changes:
        entry.tags = find_in_habit(db, Tag, changes["tag_ids"], habit)

    return save_and_report(db, habit, today, entry)


@router.delete("/entries/{entry_id}", status_code=200, response_model=EffectsOut)
def delete_entry(entry: Entry = Depends(owned_entry), today: dt.date = Depends(user_today),
                 db: Session = Depends(get_db)):
    """Deletes a session → badge changes and streaks without it."""
    habit = db.get(Habit, entry.habit_id)
    db.delete(entry)

    return save_and_report(db, habit, today)


def check_date(entry_date: dt.date, habit: Habit, today: dt.date):
    """A session cannot be in the future, nor before the habit starts → 400."""
    if entry_date > today:
        raise HTTPException(status_code=400, detail="A session cannot be in the future")
    if entry_date < habit.start_date:
        raise HTTPException(status_code=400, detail=f"The habit starts on {habit.start_date}: move its start date first")


def set_values(db: Session, entry: Entry, habit: Habit, values: dict[UUID, float]):
    """
    Typed-in values of a session, replacing the old ones:
        - Metrics of the same habit (404 / 400), and not ratios, which are calculated (400)
        - Ratios recalculated from them
    """
    metrics = find_in_habit(db, Metric, list(values), habit)

    for metric in metrics:
        if metric.kind == MetricKind.RATIO:
            raise HTTPException(status_code=400, detail=f"{metric.name} is calculated: it cannot be typed in")

    entry.values = [EntryValue(metric_id=metric.id, value=values[metric.id]) for metric in metrics]
    ratios = db.scalars(select(Metric).where(Metric.habit_id == habit.id, Metric.kind == MetricKind.RATIO)).all()
    refresh_ratios(entry, list(ratios))


def save_and_report(db: Session, habit: Habit, today: dt.date, entry: Entry | None = None) -> dict:
    """
    After a write: badges recalculated, everything saved at once → what the front needs to celebrate:
        - The session (none after a delete), the badges that changed and the habit's streaks
    """
    db.flush()
    history = load_history(db, habit.id)
    changes = recalculate_badges(db, habit, today, history)
    current, best = habit_streaks(habit, history, today)

    report = {
        "badge_changes": [BadgeChangeOut.from_change(change) for change in changes],
        "current_streak": current,
        "best_streak": best,
    }
    if entry is not None:
        report["entry"] = EntryOut.model_validate(entry)

    db.commit()
    return report
