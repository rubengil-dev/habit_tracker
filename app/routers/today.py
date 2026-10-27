"""
Daily view: every active habit with how today and its current period are going.
"""

# Imports
import datetime as dt
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import current_user, user_today
from app.models import Habit, User
from app.schemas import BadgeChangeOut, HabitOut, TodayHabitOut, TodayOut
from app.services.badges import recalculate_badges
from app.services.history import EntryFacts, load_history
from app.services.streaks import goal_so_far, habit_streaks

router = APIRouter()


@router.get("/today", status_code=200, response_model=TodayOut)
def get_today(user: User = Depends(current_user), today: dt.date = Depends(user_today), db: Session = Depends(get_db)):
    """
    Active habits, oldest first, with today's sessions, their goal so far and streaks:
        - Badges recalculated on opening: the ones that went up overnight (avoid mode) come back to celebrate
    """
    habits = db.scalars(select(Habit).where(Habit.user_id == user.id, Habit.active).order_by(Habit.created_at)).all()
    rows, changes = [], []

    for habit in habits:
        history = load_history(db, habit.id)
        changes += recalculate_badges(db, habit, today, history)
        rows.append(habit_today(habit, history, today))

    response = TodayOut(date=today, habits=rows, badge_changes=[BadgeChangeOut.from_change(change) for change in changes])
    db.commit()
    return response


def habit_today(habit: Habit, history: list[EntryFacts], today: dt.date) -> TodayHabitOut:
    """How one habit is going today."""
    period_count, goal_met = goal_so_far(habit, history, today)
    current, best = habit_streaks(habit, history, today)

    return TodayHabitOut(
        habit=HabitOut.model_validate(habit),
        today_count=sum(1 for entry in history if entry.date == today),
        period_count=period_count,
        goal_met=goal_met,
        current_streak=current,
        best_streak=best,
    )
