"""
Export: every piece of the user's data in one JSON file, as a backup.
"""

# Imports
import datetime as dt
from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import current_user, user_today
from app.models import Habit, User
from app.schemas import ExportOut

router = APIRouter()


@router.get("/export", status_code=200, response_model=ExportOut)
def export_data(response: Response, user: User = Depends(current_user), today: dt.date = Depends(user_today),
                db: Session = Depends(get_db)):
    """User, habits and everything in them (metrics, tags, sessions, badges), downloaded as a dated file."""
    habits = db.scalars(select(Habit).where(Habit.user_id == user.id).order_by(Habit.created_at)).all()
    response.headers["Content-Disposition"] = f'attachment; filename="habit-tracker-{today}.json"'

    return ExportOut.model_validate(
        {"exported_at": dt.datetime.now(dt.UTC), "user": user, "habits": habits},
        from_attributes=True,
    )
