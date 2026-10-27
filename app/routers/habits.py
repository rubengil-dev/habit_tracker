"""
Habits endpoints: CRUD; one habit comes with its current and best streak.
"""

# Imports
import datetime as dt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import current_user, owned_habit, user_today
from app.models import Entry, Habit, User
from app.schemas import HabitCreate, HabitDetailOut, HabitOut, HabitUpdate
from app.services.badges import recalculate_badges
from app.services.history import load_history
from app.services.streaks import habit_streaks

router = APIRouter()


@router.get("/habits", status_code=200, response_model=list[HabitOut])
def list_habits(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Every habit of the user, oldest first."""
    return db.scalars(select(Habit).where(Habit.user_id == user.id).order_by(Habit.created_at)).all()


@router.get("/habits/{habit_id}", status_code=200, response_model=HabitDetailOut)
def get_habit(habit: Habit = Depends(owned_habit), today: dt.date = Depends(user_today), db: Session = Depends(get_db)):
    """One habit, with its current and best streak."""
    current, best = habit_streaks(habit, load_history(db, habit.id), today)
    return HabitDetailOut(**HabitOut.model_validate(habit).model_dump(), current_streak=current, best_streak=best)


@router.post("/habits", status_code=201, response_model=HabitOut)
def create_habit(data: HabitCreate, user: User = Depends(current_user), today: dt.date = Depends(user_today),
                 db: Session = Depends(get_db)):
    """Creates a habit; it starts today unless another date is given."""
    start_date = data.start_date or today
    check_not_future(start_date, today)

    # Create
    habit = Habit(
        user_id=user.id,
        name=data.name,
        active=data.active,
        start_date=start_date,
        goal_target=data.goal_target,
        goal_period=data.goal_period,
        goal_mode=data.goal_mode,
    )
    db.add(habit)
    db.commit()
    return habit


@router.patch("/habits/{habit_id}", status_code=200, response_model=HabitOut)
def update_habit(data: HabitUpdate, habit: Habit = Depends(owned_habit), today: dt.date = Depends(user_today),
                 db: Session = Depends(get_db)):
    """Partial update; a new start date recalculates the badges, which count periods from it."""
    changes = data.model_dump(exclude_unset=True)

    if "start_date" in changes:
        check_not_future(changes["start_date"], today)
        check_no_sessions_before(db, habit, changes["start_date"])

    # Update
    for field, value in changes.items():
        setattr(habit, field, value)

    if "start_date" in changes:
        recalculate_badges(db, habit, today)

    db.commit()
    return habit


@router.delete("/habits/{habit_id}", status_code=204)
def delete_habit(habit: Habit = Depends(owned_habit), db: Session = Depends(get_db)):
    """Deletes a habit and everything in it: metrics, tags, sessions and badges."""
    db.delete(habit)
    db.commit()


def check_not_future(start_date: dt.date, today: dt.date):
    """A habit cannot start in the future → 400."""
    if start_date > today:
        raise HTTPException(status_code=400, detail="The start date cannot be in the future")


def check_no_sessions_before(db: Session, habit: Habit, start_date: dt.date):
    """The start date cannot leave sessions before it → 400."""
    first_session = db.scalar(select(func.min(Entry.date)).where(Entry.habit_id == habit.id))

    if first_session is not None and first_session < start_date:
        raise HTTPException(status_code=400, detail=f"There are sessions before {start_date}: the first one is on {first_session}")
