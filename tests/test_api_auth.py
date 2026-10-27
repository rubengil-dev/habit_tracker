"""
Login and sessions, through the API:
    - Cookie on success; the same answer for an unknown user and a wrong password
    - Lockout after 5 failures, and back in once it ends
    - Logout, expired sessions and the daily renewal
    - Every endpoint needs a session
    - The script that creates users
"""

# Imports
import datetime as dt
from sqlalchemy import select

from app.dependencies import COOKIE_NAME
from app.models import AuthSession, User
from app.services.auth import SESSION_LIFETIME
from scripts.create_user import save_user
from tests.helpers import PASSWORD, count


def log_in(client, password: str = PASSWORD, username: str = "tester"):
    """Login request → response."""
    return client.post("/auth/login", json={"username": username, "password": password})


# Login

def test_login_sets_session_cookie(anon_client, user):
    """Right password → cookie, and the API knows who you are."""
    response = log_in(anon_client)

    assert response.status_code == 204
    assert COOKIE_NAME in response.cookies
    assert anon_client.get("/auth/me").json() == {"username": "tester", "timezone": "Europe/Madrid"}


def test_wrong_password_and_unknown_user_look_the_same(anon_client, user):
    """Nobody can find out which usernames exist."""
    wrong_password = log_in(anon_client, password="not it")
    unknown_user = log_in(anon_client, username="nobody")

    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()


def test_lockout_after_five_failures(anon_client, user):
    """Five wrong passwords → 429, even with the right one, saying how long to wait."""
    for _ in range(5):
        log_in(anon_client, password="not it")

    response = log_in(anon_client)

    assert response.status_code == 429
    assert 0 < int(response.headers["Retry-After"]) <= 15 * 60


def test_login_works_again_after_lockout(anon_client, db, user):
    """Once the lockout ends, the right password works and the count starts again."""
    user.locked_until = dt.datetime.now(dt.UTC) - dt.timedelta(minutes=1)
    db.commit()

    assert log_in(anon_client).status_code == 204


def test_success_resets_failures(anon_client, db, user):
    """Four failures, a success, four more: no lockout."""
    for _ in range(4):
        log_in(anon_client, password="not it")
    log_in(anon_client)
    for _ in range(4):
        log_in(anon_client, password="not it")

    assert log_in(anon_client).status_code == 204


# Sessions

def test_logout_closes_session(client):
    """After logging out, the old cookie no longer works."""
    token = client.cookies[COOKIE_NAME]
    client.post("/auth/logout")
    client.cookies.set(COOKIE_NAME, token)

    assert client.get("/auth/me").status_code == 401


def test_expired_session_is_rejected(client, db):
    """A session past its lifetime does not work."""
    expire_sessions(db, dt.timedelta(seconds=-1))
    assert client.get("/auth/me").status_code == 401


def test_session_renewed_once_a_day(client, db):
    """Used after more than a day: valid for its full lifetime again, and a fresh cookie."""
    expire_sessions(db, SESSION_LIFETIME - dt.timedelta(days=2))

    response = client.get("/auth/me")
    db.expire_all()
    expires_at = db.scalar(select(AuthSession.expires_at))

    assert COOKIE_NAME in response.cookies
    assert expires_at > dt.datetime.now(dt.UTC) + SESSION_LIFETIME - dt.timedelta(minutes=1)


def test_every_endpoint_needs_a_session(anon_client):
    """Without a cookie: 401."""
    assert anon_client.get("/habits").status_code == 401
    assert anon_client.post("/habits", json={}).status_code == 401


# Settings

def test_timezone_can_be_changed(client):
    """Valid IANA timezone saved; an unknown one rejected."""
    assert client.patch("/auth/me", json={"timezone": "America/Mexico_City"}).json()["timezone"] == "America/Mexico_City"
    assert client.patch("/auth/me", json={"timezone": "Mars/Olympus"}).status_code == 422


# Script

def test_script_creates_user(db):
    """New user with a hashed password, never the password itself."""
    save_user(db, "newcomer", "a long password")
    db.commit()

    user = db.scalar(select(User).where(User.username == "newcomer"))
    assert user.password_hash.startswith("$argon2")


def test_script_new_password_unlocks_and_logs_out(client, db, user):
    """A new password unlocks the user and closes every open session."""
    user.locked_until = dt.datetime.now(dt.UTC) + dt.timedelta(minutes=10)
    db.commit()

    save_user(db, "tester", "a brand new password")
    db.commit()

    assert count(db, AuthSession) == 0
    assert db.get(User, user.id).locked_until is None


def expire_sessions(db, time_left: dt.timedelta):
    """Every session set to expire after time_left."""
    for session in db.scalars(select(AuthSession)):
        session.expires_at = dt.datetime.now(dt.UTC) + time_left
    db.commit()
