"""
Sessions of a habit, loaded once as plain facts for streaks and badges.
"""

# Imports
import datetime as dt
from dataclasses import dataclass
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Entry


@dataclass(frozen=True)
class EntryFacts:
    """What the calculations need from one session."""

    date: dt.date
    values: dict[UUID, float]           # metric id → value
    tag_ids: frozenset[UUID]


def load_history(db: Session, habit_id: UUID) -> list[EntryFacts]:
    """Every session of a habit, oldest first."""
    query = select(Entry).where(Entry.habit_id == habit_id).order_by(Entry.date, Entry.created_at)
    return [to_facts(entry) for entry in db.scalars(query)]


def to_facts(entry: Entry) -> EntryFacts:
    """Session row → its facts."""
    values = {value.metric_id: value.value for value in entry.values}
    return EntryFacts(entry.date, values, frozenset(tag.id for tag in entry.tags))
