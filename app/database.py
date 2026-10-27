"""
Database connection:
    - Tables base class, with constraint naming for migrations
    - Postgres engine, from the DATABASE_URL environment variable
    - Session per request
"""

# Imports
from functools import lru_cache
from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from app.config import get_settings, sqlalchemy_url

# Constraint names, so Alembic can find them in later migrations
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_N_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Tables base class."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


@lru_cache
def get_engine() -> Engine:
    """Engine, created on first use. pre_ping reconnects after Neon has gone to sleep."""
    return create_engine(sqlalchemy_url(get_settings().database_url), pool_pre_ping=True)


def get_db():
    """Session provider: one session per request, rolled back on any error."""

    db = Session(get_engine())

    try:
        yield db
    except Exception:
        db.rollback()
        raise                   # Re-raise so the handler in main.py catches it

    finally:
        db.close()
