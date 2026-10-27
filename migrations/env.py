"""
Alembic runner:
    - Database from the DATABASE_URL environment variable (or .env)
    - Tables from app/models.py, so autogenerate can compare them with the database
"""

# Imports
from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings, sqlalchemy_url
from app.database import Base
from app.models import UTCDateTime          # Also registers every table in Base.metadata

# Tables to compare against
target_metadata = Base.metadata


def run():
    """Entry point: offline writes the SQL to the screen, online runs it against the database."""
    url = sqlalchemy_url(get_settings().database_url)

    if context.is_offline_mode():
        run_offline(url)
    else:
        run_online(url)


def run_offline(url: str):
    """SQL only, without connecting (alembic upgrade head --sql)."""
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_online(url: str):
    """Migrations run against the database, all in one transaction."""
    engine = create_engine(url, poolclass=NullPool)

    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, render_item=render_item)

        with context.begin_transaction():
            context.run_migrations()


def render_item(kind, obj, autogen_context):
    """App-only column types → standard SQLAlchemy types in the migration files."""
    if kind == "type" and isinstance(obj, UTCDateTime):
        return "sa.DateTime(timezone=True)"
    return False                # Default rendering


run()
