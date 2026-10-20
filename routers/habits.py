"""
Habits endpoints: CRUD.
"""

# Imports
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Habits
from schemas import HabitCreate, HabitUpdate, HabitResponse

router = APIRouter()


@router.get("/habits", status_code=200, response_model=list[HabitResponse])
def list_habits(db: Session = Depends(get_db)):
    """Returns every habit."""

    # Query
    return db.query(Habits).all()


@router.get("/habits/{id}", status_code=200, response_model=HabitResponse)
def get_habit(id: int, db: Session = Depends(get_db)):
    """Returns one habit."""

    # Query
    habit = db.query(Habits).filter(Habits.id == id).first()

    # Existence check
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit


@router.post("/habits", status_code=201, response_model=HabitResponse)
def create_habit(data: HabitCreate, db: Session = Depends(get_db)):
    """Creates a habit."""

    # Create
    new_habit = Habits(habit=data.habit)

    # Save
    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)
    return new_habit


@router.patch("/habits/{id}", status_code=200, response_model=HabitResponse)
def update_habit(id: int, data: HabitUpdate, db: Session = Depends(get_db)):
    """Updates a habit."""

    # Query
    habit = db.query(Habits).filter(Habits.id == id).first()

    # Existence check
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")

    # Update
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(habit, key, value)

    # Save
    db.commit()
    db.refresh(habit)
    return habit


@router.delete("/habits/{id}", status_code=204)
def delete_habit(id: int, db: Session = Depends(get_db)):
    """Deletes a habit and everything under it."""

    # Query
    habit = db.query(Habits).filter(Habits.id == id).first()

    # Existence check
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")

    # Save
    db.delete(habit)
    db.commit()
