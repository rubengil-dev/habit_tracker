"""
Entries endpoints: CRUD, with badges and streak recalculation on writes.
"""

# Imports
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Entries, Habits, Metrics
from schemas import EntryCreate, EntryUpdate, EntryResponse, EntryWriteResponse
from services.badge_progress import recalculate_badges
from services.calc_streaks import calculate_habit_streak

router = APIRouter()


@router.get("/entries", status_code=200, response_model=list[EntryResponse])
def list_entries(db: Session = Depends(get_db)):
    """Returns every entry."""

    # Query
    return db.query(Entries).all()


@router.get("/habits/{habit_id}/entries", status_code=200, response_model=list[EntryResponse])
def list_entries_related(habit_id: int, db: Session = Depends(get_db)):
    """Returns every entry of a habit."""

    # Habit check
    habit = db.query(Habits).filter(Habits.id == habit_id).first()

    if habit is None:
        raise HTTPException(status_code=404, detail=f"Habit #{habit_id} not found")

    # Query
    return db.query(Entries).filter(Entries.habit_id == habit_id).all()


@router.get("/entries/{id}", status_code=200, response_model=EntryResponse)
def get_entry(id: int, db: Session = Depends(get_db)):
    """Returns one entry."""

    # Query
    entry = db.query(Entries).filter(Entries.id == id).first()

    # Existence check
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.post("/entries", status_code=201, response_model=EntryWriteResponse)
def create_entry(data: EntryCreate, db: Session = Depends(get_db)):
    """Creates an entry → badges and streak updates."""

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
    new_entry = Entries(
        habit_id=data.habit_id,
        metric_id=data.metric_id,
        value=data.value,
        date=data.date
    )

    # Save
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    # Badges recalculation
    badges_update = recalculate_badges(db, new_entry.metric_id)

    # Streak recalculation
    streak_update = calculate_habit_streak(new_entry.habit_id, db)

    return {"entry": new_entry, "badges_update": badges_update, "streak_update": streak_update}


@router.patch("/entries/{id}", status_code=200, response_model=EntryWriteResponse)
def update_entry(id: int, data: EntryUpdate, db: Session = Depends(get_db)):
    """Updates an entry → badges and streak updates."""

    # Query
    entry = db.query(Entries).filter(Entries.id == id).first()

    # Existence check
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")

    # Final foreign keys
    update_data = data.model_dump(exclude_unset=True)
    new_habit_id = update_data.get("habit_id", entry.habit_id)
    new_metric_id = update_data.get("metric_id", entry.metric_id)

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
    old_metric_id = entry.metric_id

    # Update
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(entry, key, value)

    # Save
    db.commit()
    db.refresh(entry)

    # Badges recalculation: old and new metric
    metric_ids = {old_metric_id, entry.metric_id}
    badges_update = []

    for metric_id in metric_ids:
        badges_update += recalculate_badges(db, metric_id)

    # Streak recalculation
    streak_update = calculate_habit_streak(entry.habit_id, db)

    return {"entry": entry, "badges_update": badges_update, "streak_update": streak_update}


@router.delete("/entries/{id}", status_code=200, response_model=EntryWriteResponse)
def delete_entry(id: int, db: Session = Depends(get_db)):
    """Deletes an entry → badges and streak updates."""

    # Query
    entry = db.query(Entries).filter(Entries.id == id).first()

    # Existence check
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")

    # Ids kept before deletion
    metric_id = entry.metric_id
    habit_id = entry.habit_id

    # Save
    db.delete(entry)
    db.commit()

    # Badges recalculation
    badges_update = recalculate_badges(db, metric_id)

    # Streak recalculation
    streak_update = calculate_habit_streak(habit_id, db)

    return {"badges_update": badges_update, "streak_update": streak_update}
