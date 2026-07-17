from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Badges, Habits
from schemas import BadgeCreate, BadgeUpdate

router = APIRouter()

# GET ALL BADGES
@router.get("/badges", status_code=200)
def list_badges(db: Session = Depends(get_db)):
    return db.query(Badges).all()

# GET ALL BADGES FROM ONE HABIT
@router.get("/habits/{habit_id}/badges", status_code=200)
def list_badges_related(habit_id: int, db: Session = Depends(get_db)):
    habit = db.query(Habits).filter(Habits.id == habit_id).first()
    if habit is None:
        raise HTTPException(status_code=404, detail=f"Habit #{habit_id} not found")

    return db.query(Badges).filter(Badges.habit_id == habit_id).all()

# GET ONE BADGE
@router.get("/badges/{id}", status_code=200)
def get_badge(id: int, db: Session = Depends(get_db)):
    badge = db.query(Badges).filter(Badges.id == id).first()

    if badge is None:
        raise HTTPException(status_code=404, detail="Badge not found")
    return badge

# CREATE BADGE
@router.post("/badges", status_code=201)
def create_badge(data: BadgeCreate, db: Session = Depends(get_db)):
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
        current_value=data.current_value,
        current_tier=data.current_tier,
        frequency_target=data.frequency_target,
        frequency_period=data.frequency_period,
        higher_is_better=data.higher_is_better
    )

    db.add(new_badge)
    db.commit()
    db.refresh(new_badge)
    return new_badge

# UPDATE BADGE
@router.patch("/badge/{id}", status_code=200)
def update_badge(id: int, data: BadgeUpdate, db: Session = Depends(get_db)):
    badge = db.query(Badges).filter(Badges.id == id).first()

    if badge is None:
        raise HTTPException(status_code=404, detail="Badge not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(badge, key, value)

    db.commit()
    db.refresh(badge)
    return badge

# DELETE BADGE
@router.delete("/badges/{id}", status_code=204)
def delete_badge(id: int, db: Session = Depends(get_db)):
    badge = db.query(Badges).filter(Badges.id == id).first()

    if badge is None:
        raise HTTPException(status_code=404, detail="Badge not found")
    
    db.delete(badge)
    db.commit()