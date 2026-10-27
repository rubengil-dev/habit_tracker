"""
Test fixtures:
    - Safety check: never run against the app's own database
    - Empty database per test: SQLite in memory, or TEST_DATABASE_URL for a real Postgres
    - A user and a habit ready to use
    - API clients on that database, with today fixed: anonymous, or logged in as the user
"""

# Imports
import datetime as dt
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config import get_settings, sqlalchemy_url
from app.database import Base, get_db
from app.dependencies import COOKIE_NAME, user_today
from app.enums import Period
from app.main import app
from app.models import Habit, User
from app.services.auth import open_session
from tests.helpers import PASSWORD_HASH, TEST_DATABASE_URL, TODAY, add


def pytest_configure(config):
    """The tests drop every table: they refuse to start if pointed at the app's database (.env)."""
    if TEST_DATABASE_URL.startswith("sqlite"):
        return

    try:
        app_url = get_settings().database_url
    except ValidationError:
        return                  # No .env: nothing to protect

    if sqlalchemy_url(app_url) == sqlalchemy_url(TEST_DATABASE_URL):
        pytest.exit("TEST_DATABASE_URL is the app's own database: the tests would wipe it", returncode=1)


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
    return add(db, User(username="tester", password_hash=PASSWORD_HASH))


@pytest.fixture
def habit(db, user):
    """Daily habit of the test user."""
    return add(db, Habit(user_id=user.id, name="Run", start_date=dt.date(2026, 1, 1), goal_target=1, goal_period=Period.DAILY))


@pytest.fixture
def anon_client(engine):
    """API client without a session; https, so the secure cookie travels."""
    app.dependency_overrides[get_db] = sessions_on(engine)
    app.dependency_overrides[user_today] = lambda: TODAY

    with TestClient(app, base_url="https://testserver") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def client(anon_client, engine, user):
    """API client logged in as the test user (session opened straight in the database, to skip Argon2)."""
    with Session(engine) as db:
        token = open_session(db, db.get(User, user.id), dt.datetime.now(dt.UTC))
        db.commit()

    anon_client.cookies.set(COOKIE_NAME, token)
    return anon_client


@pytest.fixture
def set_today():
    """Moves the API's today: set_today(date)."""
    def move(day: dt.date):
        app.dependency_overrides[user_today] = lambda: day
    return move


def sessions_on(engine):
    """get_db for the tests: one session per request on the test database."""
    def get_test_db():
        db = Session(engine)
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    return get_test_db


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
