"""
Test fixtures:
    - Empty database per test: SQLite in memory, or TEST_DATABASE_URL for a real Postgres
    - A user and a habit ready to use
"""

# Imports
import datetime as dt
import os
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config import sqlalchemy_url
from app.database import Base
from app.enums import Period
from app.models import Habit, User
from tests.helpers import add

# SQLite in memory by default; set TEST_DATABASE_URL to run against Postgres
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "sqlite://")


@pytest.fixture
def engine():
    """Empty database with every table, dropped after the test."""
    engine = build_engine(sqlalchemy_url(TEST_DATABASE_URL))
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db(engine):
    """Session on the test database."""
    with Session(engine) as session:
        yield session


@pytest.fixture
def user(db):
    """Test user."""
    return add(db, User(username="tester", password_hash="not-a-real-hash"))


@pytest.fixture
def habit(db, user):
    """Daily habit of the test user."""
    return add(db, Habit(user_id=user.id, name="Run", start_date=dt.date(2026, 1, 1), goal_target=1, goal_period=Period.DAILY))


def build_engine(url: str):
    """Engine for the test database. SQLite needs one shared connection and foreign keys switched on."""
    if not url.startswith("sqlite"):
        return create_engine(url)

    engine = create_engine(url, poolclass=StaticPool, connect_args={"check_same_thread": False})
    event.listen(engine, "connect", enable_foreign_keys)
    return engine


def enable_foreign_keys(dbapi_connection, connection_record):
    """SQLite foreign keys switch, needed for cascade deletion. Postgres has them always on."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
