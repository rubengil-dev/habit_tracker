from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Habits
from schemas import HabitCreate, HabitUpdate

router = APIRouter()

# GET ALL HABITS
@router.get("/habits", status_code=200)
def list_habits(db: Session = Depends(get_db)):
    return db.query(Habits).all()

# GET ONE HABIT
@router.get("/habits/{id}", status_code=200)
def get_habit(id: int, db: Session = Depends(get_db)):
    habit = db.query(Habits).filter(Habits.id == id).first()

    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit

# CREATE HABIT
@router.post("/habits", status_code=201)
def create_habit(data: HabitCreate, db: Session = Depends(get_db)):
    new_habit = Habits(habit=data.habit)

    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)
    return new_habit

# UPDATE HABITS
@router.patch("/habits/{id}", status_code=200)
def update_habit(id: int, data: HabitUpdate, db: Session = Depends(get_db)):
    habit = db.query(Habits).filter(Habits.id == id).first()

    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(habit, key, value)

    db.commit()
    db.refresh(habit)
    return habit

# DELETE HABIT
@router.delete("/habits/{id}", status_code=204)
def delete_habit(id: int, db: Session = Depends(get_db)):
    habit = db.query(Habits).filter(Habits.id == id).first()

    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    db.delete(habit)
    db.commit()