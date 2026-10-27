"""
Ratio metrics (A ÷ B), calculated when a session is saved:
    - Value in one session
    - Ratios of a session refreshed after its values change
    - A new ratio filled in for every past session of its habit
"""

# Imports
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Entry, EntryValue, Metric


def ratio_value(values: dict[UUID, float], metric: Metric) -> float | None:
    """A ÷ B in one session; None if A or B is missing, or B is 0."""
    a = values.get(metric.operand_a_id)
    b = values.get(metric.operand_b_id)

    if a is None or not b:
        return None
    return a / b


def refresh_ratios(entry: Entry, ratio_metrics: list[Metric]):
    """Ratio values of a session, recalculated from its typed-in values: added, updated or removed."""
    ratio_ids = {metric.id for metric in ratio_metrics}
    stored = {value.metric_id: value for value in entry.values}
    typed = {metric_id: row.value for metric_id, row in stored.items() if metric_id not in ratio_ids}

    for metric in ratio_metrics:
        ratio = ratio_value(typed, metric)
        row = stored.get(metric.id)

        if ratio is None and row is not None:
            entry.values.remove(row)
        elif ratio is not None and row is not None:
            row.value = ratio
        elif ratio is not None:
            entry.values.append(EntryValue(metric_id=metric.id, value=ratio))


def backfill_ratio(db: Session, metric: Metric):
    """New ratio metric → its value in every past session of the habit."""
    db.flush()                  # The metric needs its id before it is used

    for entry in db.scalars(select(Entry).where(Entry.habit_id == metric.habit_id)):
        refresh_ratios(entry, [metric])
