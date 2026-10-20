"""
Database connection:
    - SQLite engine
    - Session per request
"""

# Imports
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

# Engine
engine = create_engine("sqlite:///habits.db")


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Foreign keys activator, needed for cascade deletion."""

    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Session factory
SessionLocal = sessionmaker(bind = engine)

# Tables base class
Base = declarative_base()


def get_db():
    """Session provider: one session per request, rolled back on any error."""

    db = SessionLocal()

    try:
        yield db
    except Exception:
        db.rollback()
        raise                   # Re-raise so the handler in main.py catches it

    finally:
        db.close()
