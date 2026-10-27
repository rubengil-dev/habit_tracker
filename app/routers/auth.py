"""
Auth endpoints: login, logout and the logged-in user's settings.
"""

# Imports
import datetime as dt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import COOKIE_NAME, current_user, set_session_cookie
from app.models import User
from app.schemas import LoginIn, UserOut, UserUpdate
from app.services.auth import LoginLocked, close_session, login

router = APIRouter()


@router.post("/auth/login", status_code=204)
def log_in(data: LoginIn, response: Response, db: Session = Depends(get_db)):
    """Password check → session cookie for 3 months; 401 if wrong, 429 while locked out."""
    now = dt.datetime.now(dt.UTC)

    try:
        token = login(db, data.username, data.password, now)
    except LoginLocked as locked:
        wait = int((locked.until - now).total_seconds()) + 1
        raise HTTPException(status_code=429, detail="Too many failed logins, try again later",
                            headers={"Retry-After": str(wait)})

    # Saved either way: a failure counts towards the lockout
    db.commit()

    if token is None:
        raise HTTPException(status_code=401, detail="Wrong username or password")
    set_session_cookie(response, token)


@router.post("/auth/logout", status_code=204)
def log_out(request: Request, response: Response, db: Session = Depends(get_db)):
    """Session closed and cookie removed."""
    token = request.cookies.get(COOKIE_NAME)

    if token:
        close_session(db, token)
        db.commit()
    response.delete_cookie(COOKIE_NAME)


@router.get("/auth/me", status_code=200, response_model=UserOut)
def get_me(user: User = Depends(current_user)):
    """Logged-in user."""
    return user


@router.patch("/auth/me", status_code=200, response_model=UserOut)
def update_me(data: UserUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Settings of the logged-in user (timezone)."""

    # Update
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    return user
