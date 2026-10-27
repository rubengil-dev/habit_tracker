"""
FastAPI dependencies shared by the routers:
    - Logged-in user, from the session cookie (401 otherwise), and their today
    - Rows owned by that user (404 otherwise)
    - Rows referenced in a body: they exist (404) and belong to the same habit (400)
"""

# Imports
import datetime as dt
from uuid import UUID
from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Badge, Entry, Habit, Metric, Tag, User
from app.services.auth import SESSION_LIFETIME, find_session, renew_if_due
from app.services.periods import local_today

# Session cookie
COOKIE_NAME = "session"


# Logged-in user

def current_user(request: Request, response: Response, db: Session = Depends(get_db)) -> User:
    """User of the session cookie; the session is renewed for 3 months once a day."""
    token = request.cookies.get(COOKIE_NAME)
    now = dt.datetime.now(dt.UTC)
    session = find_session(db, token, now) if token else None

    if session is None:
        raise HTTPException(status_code=401, detail="Not logged in")

    if renew_if_due(session, now):
        db.commit()
        set_session_cookie(response, token)

    return session.user


def user_today(user: User = Depends(current_user)) -> dt.date:
    """Today in the user's timezone."""
    return local_today(user.timezone)


def set_session_cookie(response: Response, token: str):
    """
    Session cookie, valid 3 months:
        - httponly: page scripts cannot read it
        - secure: only over https (browsers also allow it on localhost)
        - samesite lax: other websites cannot send it in their requests
    """
    response.set_cookie(
        COOKIE_NAME, token, max_age=int(SESSION_LIFETIME.total_seconds()),
        httponly=True, secure=True, samesite="lax",
    )


# Rows of the path, owned by the user

def owned_habit(habit_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Habit:
    """Habit of the path."""
    return find_owned(db, Habit, habit_id, user)


def owned_metric(metric_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Metric:
    """Metric of the path."""
    return find_owned(db, Metric, metric_id, user)


def owned_tag(tag_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Tag:
    """Tag of the path."""
    return find_owned(db, Tag, tag_id, user)


def owned_entry(entry_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Entry:
    """Session of the path."""
    return find_owned(db, Entry, entry_id, user)


def owned_badge(badge_id: UUID, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Badge:
    """Badge of the path."""
    return find_owned(db, Badge, badge_id, user)


def find_owned(db: Session, model, row_id: UUID, user: User):
    """Row with that id, if the user owns it (directly, or through its habit) → 404 otherwise."""
    query = select(model).where(model.id == row_id)

    if model is Habit:
        query = query.where(Habit.user_id == user.id)
    else:
        query = query.join(Habit, model.habit_id == Habit.id).where(Habit.user_id == user.id)

    row = db.scalar(query)
    if row is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return row


# Rows referenced in a body

def find_in_habit(db: Session, model, ids: list[UUID], habit: Habit) -> list:
    """
    Rows a body points to (metrics, tags), in the given order:
        - 404 if one does not exist for this user
        - 400 if one belongs to another habit
    """
    rows = {row.id: row for row in db.scalars(
        select(model).join(Habit, model.habit_id == Habit.id)
        .where(model.id.in_(ids), Habit.user_id == habit.user_id)
    )}

    for row_id in ids:
        if row_id not in rows:
            raise HTTPException(status_code=404, detail=f"{model.__name__} {row_id} not found")
        if rows[row_id].habit_id != habit.id:
            raise HTTPException(status_code=400, detail=f"{model.__name__} {row_id} belongs to another habit")

    return [rows[row_id] for row_id in ids]
