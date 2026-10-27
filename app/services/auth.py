"""
Login and sessions:
    - Passwords hashed with Argon2
    - Lockout after repeated failures
    - Session tokens: random, stored only as a SHA-256 hash, valid 3 months and renewed on use
"""

# Imports
import datetime as dt
import hashlib
import secrets
from functools import lru_cache
from pwdlib import PasswordHash
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import AuthSession, User

# Rules
MAX_FAILED_LOGINS = 5
LOCKOUT = dt.timedelta(minutes=15)
SESSION_LIFETIME = dt.timedelta(days=90)        # Unused for longer → log in again
RENEW_EVERY = dt.timedelta(days=1)              # At most one renewal write a day

# Argon2, with the library's recommended settings
password_hasher = PasswordHash.recommended()


class LoginLocked(Exception):
    """Too many failed logins: the user is locked out until a given moment."""

    def __init__(self, until: dt.datetime):
        """Moment the lockout ends."""
        super().__init__(f"Locked out until {until}")
        self.until = until


def login(db: Session, username: str, password: str, now: dt.datetime) -> str | None:
    """
    Password check → new session token, or None if it fails:
        - An unknown user and a wrong password look the same from outside
        - Raises LoginLocked while the user is locked out
    """
    user = db.scalar(select(User).where(User.username == username))

    if user is None:
        password_hasher.verify(password, dummy_hash())          # Same time as a real check
        return None

    if user.locked_until is not None and user.locked_until > now:
        raise LoginLocked(user.locked_until)

    if not password_hasher.verify(password, user.password_hash):
        register_failure(user, now)
        return None

    user.failed_logins = 0
    user.locked_until = None
    return open_session(db, user, now)


def find_session(db: Session, token: str, now: dt.datetime) -> AuthSession | None:
    """Session of a cookie token, if it exists and has not expired."""
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == hash_token(token)))

    if session is None or session.expires_at <= now:
        return None
    return session


def renew_if_due(session: AuthSession, now: dt.datetime) -> bool:
    """Session extended to its full lifetime again, once a day at most → whether it was renewed."""
    if session.expires_at - now > SESSION_LIFETIME - RENEW_EVERY:
        return False

    session.expires_at = now + SESSION_LIFETIME
    return True


def close_session(db: Session, token: str):
    """Logout: the session of a token stops working."""
    db.execute(delete(AuthSession).where(AuthSession.token_hash == hash_token(token)))


def hash_password(password: str) -> str:
    """Password → Argon2 hash, the only thing stored."""
    return password_hasher.hash(password)


# Helpers

def register_failure(user: User, now: dt.datetime):
    """One more failed login; the last allowed one locks the user out and resets the count."""
    user.failed_logins += 1

    if user.failed_logins >= MAX_FAILED_LOGINS:
        user.locked_until = now + LOCKOUT
        user.failed_logins = 0


def open_session(db: Session, user: User, now: dt.datetime) -> str:
    """New session for a user → its token; their expired sessions are cleared on the way."""
    db.execute(delete(AuthSession).where(AuthSession.user_id == user.id, AuthSession.expires_at <= now))

    token = secrets.token_urlsafe(32)
    db.add(AuthSession(user_id=user.id, token_hash=hash_token(token), expires_at=now + SESSION_LIFETIME))
    return token


def hash_token(token: str) -> str:
    """Token → SHA-256: a stolen copy of the database does not give working cookies."""
    return hashlib.sha256(token.encode()).hexdigest()


@lru_cache
def dummy_hash() -> str:
    """Hash to check against when the user does not exist, made once."""
    return password_hasher.hash("not a real password")
