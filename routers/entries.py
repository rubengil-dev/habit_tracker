from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Entries, Habits, Badges, Metrics
from schemas import EntryCreate, EntryUpdate
from services.badge_progress import calculation_router
from services.calc_streaks import calculate_habit_streak

router = APIRouter()

# GET ALL ENTRIES
@router.get("/entries", status_code=200)
def list_entries(db: Session = Depends(get_db)):
    """Returns every single entry created."""

    # Query itself
    return db.query(Entries).all()

# GET ALL ENTRIES FROM ONE HABIT
@router.get("/habits/{habit_id}/entries", status_code=200)
def list_entries_related(habit_id: int, db: Session = Depends(get_db)):
    """Returns every single entry created for a concrete habit."""

    # Habit existence check
    habit = db.query(Habits).filter(Habits.id == habit_id).first()

    if habit is None:
        raise HTTPException(status_code=404, detail=f"Habit #{habit_id} not found")

    # Query itself
    return db.query(Entries).filter(Entries.habit_id == habit_id).all()

# GET ONE ENTRY
@router.get("/entries/{id}", status_code=200)
def get_entry(id: int, db: Session = Depends(get_db)):
    """Returns only one entry."""

    # Query itself
    entry = db.query(Entries).filter(Entries.id == id).first()

    # Error managing if entry doesnt exists
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry



# BADGE RECALCULATION
def recalculate_badges(db: Session, metric_id: int) -> list[dict]:
    """ 1. Finds every badge linked to a metric. 
        2. Recalculates.
        3. Saves new value and tier.
        4. Reports whether its tier changed."""
    
    # Obtains affected badges
    affected_badges = db.query(Badges).filter(Badges.metric_id == metric_id).all()
    results = []

    # For each badge, saves previous values and tiers and calculates new ones
    for badge in affected_badges:
        old_tier = badge.current_tier                                   
        new_value, new_tier = calculation_router(db, badge)

        # Saving new values
        badge.current_value = new_value
        badge.current_tier = new_tier

        # Necesary to know if tier changed
        results.append({
            "badge_id": badge.id,
            "current_value": new_value,
            "old_tier": old_tier,
            "new_tier": new_tier,
            "tier_changed": old_tier != new_tier
        })

    # DataBase Update
    db.commit()
    return results

# CREATE ENTRY
@router.post("/entries", status_code=201)
def create_entry(data: EntryCreate, db: Session = Depends(get_db)):
    """Creates a new entry."""

    # Habit existence check
    habit = db.query(Habits).filter(Habits.id == data.habit_id).first()

    if habit is None:
        raise HTTPException(status_code=404, detail=f"Habit #{data.habit_id} not found")

    # Metric existence check
    metric = db.query(Metrics).filter(Metrics.id == data.metric_id).first()

    if metric is None:
        raise HTTPException(status_code=404, detail=f"Metric #{data.metric_id} not found")

    # Metric belonging to Habit check
    if metric.habit_id != data.habit_id:
        raise HTTPException(status_code=400, detail="metric_id does not belong to habit_id")
    
    # Entry creation
    new_entry = Entries(
        habit_id=data.habit_id,
        metric_id=data.metric_id,
        value=data.value,
        date=data.date
    )

    # DataBase update
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    # Recalculates badge's progress
    badges_update = recalculate_badges(db, new_entry.metric_id)

    # Recalculates habit's streaks
    streak_update = calculate_habit_streak(new_entry.habit_id, db)

    return {"entry": new_entry, "badges_update": badges_update, "streak_update": streak_update}

# UPDATE ENTRY
@router.patch("/entries/{id}", status_code=200)
def update_entry(id: int, data: EntryUpdate, db: Session = Depends(get_db)):
    """Updates an existing entry using a loop (model_dump)."""

    # Query itself
    entry = db.query(Entries).filter(Entries.id == id).first()

    # Error managing if metric doesnt exists
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    # Resolve the final habit_id / metric_id this entry would have after the update
    update_data = data.model_dump(exclude_unset=True)
    new_habit_id = update_data.get("habit_id", entry.habit_id)
    new_metric_id = update_data.get("metric_id", entry.metric_id)

    # Check if new habit still exists
    if "habit_id" in update_data:
        habit = db.query(Habits).filter(Habits.id == new_habit_id).first()
        if habit is None:
            raise HTTPException(status_code=404, detail=f"Habit #{new_habit_id} not found")

    # Check if new metric still exists
    if "metric_id" in update_data:
        metric = db.query(Metrics).filter(Metrics.id == new_metric_id).first()
        if metric is None:
            raise HTTPException(status_code=404, detail=f"Metric #{new_metric_id} not found")

    # If there were any changes, check Metric still belonds to Habit
    if "habit_id" in update_data or "metric_id" in update_data:
        metric = db.query(Metrics).filter(Metrics.id == new_metric_id).first()
        if metric.habit_id != new_habit_id:
            raise HTTPException(status_code=400, detail="metric_id does not belong to habit_id")


    # Saving for later
    old_metric_id = entry.metric_id

    # Update itself
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(entry, key, value)

    # DataBase Update
    db.commit()
    db.refresh(entry)

    # Recalculate badges for both the old and new metric_id, in case metric_id itself changed
    metric_ids = {old_metric_id, entry.metric_id}
    badges_update = []

    for metric_id in metric_ids:
        badges_update += recalculate_badges(db, metric_id)

    # Recalculates streak, using the entry's current (post-update) habit_id
    streak_update = calculate_habit_streak(entry.habit_id, db)

    return {"entry": entry, "badges_update": badges_update, "streak_update": streak_update}


# DELETE ENTRY
@router.delete("/entries/{id}", status_code=200)
def delete_entry(id: int, db: Session = Depends(get_db)):
    """Deletes an existing entry."""

    # Query itself
    entry = db.query(Entries).filter(Entries.id == id).first()

    # Error managing if metric doesnt exists
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")

    # DataBase update
    metric_id = entry.metric_id
    habit_id = entry.habit_id

    db.delete(entry)
    db.commit()

    # Recalculates badge's progress
    badges_update = recalculate_badges(db, metric_id)

    # Recalculates habit's streaks
    streak_update = calculate_habit_streak(habit_id, db)

    return {"badges_update": badges_update, "streak_update": streak_update}