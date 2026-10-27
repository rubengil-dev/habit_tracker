"""
Migrations build the same database as app/models.py:
    - Catches a table change saved without its migration
    - Postgres only (migrations target it): skipped on SQLite
"""

# Imports
import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from app.config import ROOT, get_settings, sqlalchemy_url
from app.database import Base
from tests.helpers import TEST_DATABASE_URL

pytestmark = pytest.mark.skipif(TEST_DATABASE_URL.startswith("sqlite"), reason="Migrations target Postgres")


@pytest.fixture
def alembic_config(monkeypatch):
    """Alembic pointed at the test database, which is left empty afterwards."""
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    get_settings.cache_clear()
    config = Config(str(ROOT / "alembic.ini"))

    yield config

    command.downgrade(config, "base")
    get_settings.cache_clear()


def test_migrations_build_the_models(alembic_config):
    """Every migration applied on an empty database → no difference with models.py."""
    command.upgrade(alembic_config, "head")

    engine = create_engine(sqlalchemy_url(TEST_DATABASE_URL))
    with engine.connect() as connection:
        differences = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    engine.dispose()

    assert differences == []
