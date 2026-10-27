"""
Settings read from environment variables:
    - Local: the .env file at the project root
    - Production: Vercel's environment variables
"""

# Imports
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root, so .env is found whatever folder the app starts from
ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Environment variables used by the app."""

    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    database_url: str


@lru_cache
def get_settings() -> Settings:
    """Settings, read once on first use, so importing the app needs no .env (tests)."""
    return Settings()


def sqlalchemy_url(url: str) -> str:
    """
    Driver adder, so Neon's URL can be pasted as is:
        Example: postgresql://… → postgresql+psycopg://…
    """
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url.removeprefix(prefix)
    return url
