"""
Settings: Neon's connection string can be pasted as is.
"""

# Imports
import pytest

from app.config import sqlalchemy_url


@pytest.mark.parametrize(("url", "expected"), [
    ("postgresql://user:pass@host/db?sslmode=require",  "postgresql+psycopg://user:pass@host/db?sslmode=require"),
    ("postgres://user:pass@host/db",                    "postgresql+psycopg://user:pass@host/db"),
    ("postgresql+psycopg://user:pass@host/db",          "postgresql+psycopg://user:pass@host/db"),
    ("sqlite://",                                       "sqlite://"),
])
def test_driver_added_to_postgres_urls(url, expected):
    """Postgres URLs get the psycopg driver; the rest stay as they are."""
    assert sqlalchemy_url(url) == expected
