"""
Ratio metrics (A ÷ B):
    - Value in one session, empty when A or B is missing
    - Refreshed when the session's values change
    - Filled in for every past session when the ratio is created
"""

# Imports
import datetime as dt
from uuid import uuid4

from app.enums import MetricKind
from app.models import Entry, EntryValue, Metric
from app.services.ratios import backfill_ratio, ratio_value, refresh_ratios
from tests.helpers import add

# Pace = time ÷ distance (seconds per km)
TIME, KM = uuid4(), uuid4()
PACE = Metric(id=uuid4(), name="Pace", kind=MetricKind.RATIO, operand_a_id=TIME, operand_b_id=KM)


def test_ratio_value():
    """30 minutes over 10 km → 180 s/km; empty without one of them, or with B = 0."""
    assert ratio_value({TIME: 1800, KM: 10}, PACE) == 180
    assert ratio_value({KM: 10}, PACE) is None
    assert ratio_value({TIME: 1800, KM: 0}, PACE) is None


def test_refresh_adds_updates_and_removes():
    """The ratio follows the typed-in values of the session."""
    entry = Entry(values=[EntryValue(metric_id=TIME, value=1800), EntryValue(metric_id=KM, value=10)])

    refresh_ratios(entry, [PACE])
    assert stored(entry) == {TIME: 1800, KM: 10, PACE.id: 180}

    stored_row(entry, KM).value = 9
    refresh_ratios(entry, [PACE])
    assert stored(entry)[PACE.id] == 200

    entry.values.remove(stored_row(entry, TIME))
    refresh_ratios(entry, [PACE])
    assert stored(entry) == {KM: 9}


def test_new_ratio_fills_past_sessions(db, habit):
    """Created on a habit with history: calculated for every past session that has A and B."""
    time = add(db, Metric(habit_id=habit.id, name="Time", kind=MetricKind.DURATION))
    km = add(db, Metric(habit_id=habit.id, name="Km", unit="km", kind=MetricKind.NUMBER))
    add(db,
        Entry(habit_id=habit.id, date=dt.date(2026, 10, 5), values=[EntryValue(metric_id=time.id, value=1500), EntryValue(metric_id=km.id, value=5)]),
        Entry(habit_id=habit.id, date=dt.date(2026, 10, 6), values=[EntryValue(metric_id=time.id, value=3000), EntryValue(metric_id=km.id, value=10)]),
        Entry(habit_id=habit.id, date=dt.date(2026, 10, 7), values=[EntryValue(metric_id=km.id, value=8)]),
    )

    pace = Metric(habit_id=habit.id, name="Pace", kind=MetricKind.RATIO, operand_a_id=time.id, operand_b_id=km.id)
    db.add(pace)
    backfill_ratio(db, pace)
    db.commit()

    paces = db.query(EntryValue.value).filter(EntryValue.metric_id == pace.id).all()
    assert sorted(value for (value,) in paces) == [300, 300]


def stored(entry: Entry) -> dict:
    """Values of a session: metric id → value."""
    return {row.metric_id: row.value for row in entry.values}


def stored_row(entry: Entry, metric_id) -> EntryValue:
    """Value row of one metric in a session."""
    return next(row for row in entry.values if row.metric_id == metric_id)
