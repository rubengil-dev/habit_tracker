from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Habits
from schemas import HabitCreate, HabitUpdate

router = APIRouter()

# GET ALL HABITS
@router.get("/habits", status_code=200)
def list_habits(db: Session = Depends(get_db)):
    """Returns every single habit created."""

    # Query itself
    return db.query(Habits).all()

# GET ONE HABIT
@router.get("/habits/{id}", status_code=200)
def get_habit(id: int, db: Session = Depends(get_db)):
    """Returns one habit."""

    # Query itself
    habit = db.query(Habits).filter(Habits.id == id).first()

    # Error managing if habit doesnt exists
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit

# CREATE HABIT
@router.post("/habits", status_code=201)
def create_habit(data: HabitCreate, db: Session = Depends(get_db)):
    """Creates a new habit."""

    # Habit creation
    new_habit = Habits(habit=data.habit)

    # DataBase update
    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)
    return new_habit

# UPDATE HABITS
@router.patch("/habits/{id}", status_code=200)
def update_habit(id: int, data: HabitUpdate, db: Session = Depends(get_db)):
    """Updates an existing habit using a loop (model_dump)."""

    # Query itself
    habit = db.query(Habits).filter(Habits.id == id).first()

    # Error managing if habit doesnt exists
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")

    # Update itself
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(habit, key, value)

    # DataBase Update
    db.commit()
    db.refresh(habit)
    return habit

# DELETE HABIT
@router.delete("/habits/{id}", status_code=204)
def delete_habit(id: int, db: Session = Depends(get_db)):
    """Deletes an existing habit."""

    # Query itself
    habit = db.query(Habits).filter(Habits.id == id).first()

    # Error managing if habit doesnt exists
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    # DataBase Update
    db.delete(habit)
    db.commit()