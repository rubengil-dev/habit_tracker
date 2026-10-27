"""
Helpers shared by the tests:
    - Test database and the test user's password
    - Rows saver, rejection check for database rules and row counter
    - Unsaved habits, badges and session facts, for the calculations
"""

# Imports
import datetime as dt
import os
import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.enums import GoalMode, Tier
from app.models import Badge, Habit
from app.services.auth import hash_password
from app.services.history import EntryFacts

# SQLite in memory by default; set TEST_DATABASE_URL to run against a throwaway Postgres
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "sqlite://")

# Today for the API tests: a Monday
TODAY = dt.date(2026, 10, 26)

# Hashed once: Argon2 is slow on purpose
PASSWORD = "correct horse battery"
PASSWORD_HASH = hash_password(PASSWORD)

# Tier thresholds that go up, for counts and "higher is better"
ASCENDING = dict(unlocked=1, bronze=5, silver=10, gold=50, diamond=100)


def add(db: Session, *objects):
    """Rows saver: adds and commits → the last object, for one-liners."""
    db.add_all(objects)
    db.commit()
    return objects[-1]


def assert_rejected(db: Session, *objects):
    """Rows that break a database rule → IntegrityError; the session is then cleaned for the next step."""
    db.add_all(objects)
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def count(db: Session, table) -> int:
    """Rows in a table (model class or Table)."""
    return db.scalar(select(func.count()).select_from(table))


def make_habit(**fields) -> Habit:
    """Unsaved habit, with the defaults the database would set."""
    defaults = dict(name="Habit", active=True, goal_mode=GoalMode.MIN)
    return Habit(**(defaults | fields))


def make_badge(**fields) -> Badge:
    """Unsaved badge, with the defaults the database would set."""
    defaults = dict(name="Badge", higher_is_better=True, untagged_only=False, current_tier=Tier.LOCKED) | ASCENDING
    return Badge(**(defaults | fields))


def facts(day: dt.date, values: dict | None = None, tags: tuple = ()) -> EntryFacts:
    """Facts of one unsaved session."""
    return EntryFacts(day, values or {}, frozenset(tags))
