from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Badges, Habits, Metrics
from schemas import BadgeCreate, BadgeUpdate
from services.badge_progress import recalculate_badges

router = APIRouter()

# GET ALL BADGES
@router.get("/badges", status_code=200)
def list_badges(db: Session = Depends(get_db)):
    """Returns every single badge created."""

    # Query itself
    return db.query(Badges).all()

# GET ALL BADGES FROM ONE HABIT
@router.get("/habits/{habit_id}/badges", status_code=200)
def list_badges_related(habit_id: int, db: Session = Depends(get_db)):
    """Returns every single badge created for a concrete habit."""

    # Habit existence check
    habit = db.query(Habits).filter(Habits.id == habit_id).first()

    if habit is None:
        raise HTTPException(status_code=404, detail=f"Habit #{habit_id} not found")

    # Query itself
    return db.query(Badges).filter(Badges.habit_id == habit_id).all()

# GET ONE BADGE
@router.get("/badges/{id}", status_code=200)
def get_badge(id: int, db: Session = Depends(get_db)):
    """Returns only one badge."""

    # Query itself
    badge = db.query(Badges).filter(Badges.id == id).first()

    # Error managing if badge doesnt exists
    if badge is None:
        raise HTTPException(status_code=404, detail="Badge not found")
    return badge

# CREATE BADGE
@router.post("/badges", status_code=201)
def create_badge(data: BadgeCreate, db: Session = Depends(get_db)):
    """Creates a new badge."""

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
    
    # Badge creation
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

    # DataBase update
    db.add(new_badge)
    db.commit()
    db.refresh(new_badge)

    recalculate_badges(db, new_badge.metric_id)
    return new_badge

# UPDATE BADGE
@router.patch("/badges/{id}", status_code=200)
def update_badge(id: int, data: BadgeUpdate, db: Session = Depends(get_db)):
    """Updates an existing badge using a loop (model_dump)."""

    # Query itself
    badge = db.query(Badges).filter(Badges.id == id).first()

    # Error managing if badge doesnt exists
    if badge is None:
        raise HTTPException(status_code=404, detail="Badge not found")
    
    # Resolve the final habit_id / metric_id this badge would have after the update
    update_data = data.model_dump(exclude_unset=True)
    new_habit_id = update_data.get("habit_id", badge.habit_id)
    new_metric_id = update_data.get("metric_id", badge.metric_id)

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
    old_metric_id = badge.metric_id

    # Update itself
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(badge, key, value)

    db.commit()
    db.refresh(badge)

    metric_ids = {old_metric_id, badge.metric_id}
    for metric_id in metric_ids:
        recalculate_badges(db, metric_id)

    return badge

# DELETE BADGE
@router.delete("/badges/{id}", status_code=204)
def delete_badge(id: int, db: Session = Depends(get_db)):
    """Deletes an existing badge."""

    # Query itself
    badge = db.query(Badges).filter(Badges.id == id).first()

    # Error managing if metric doesnt exists
    if badge is None:
        raise HTTPException(status_code=404, detail="Badge not found")

    # DataBase update
    db.delete(badge)
    db.commit()