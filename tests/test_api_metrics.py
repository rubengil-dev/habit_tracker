"""
Metrics through the API:
    - Number, duration and ratio; a new ratio filled in for past sessions
    - Ratio operands: of the same habit, existing, and not ratios
    - Name and unit editable; kind and habit fixed (v1 bug 6)
    - Deleting a metric takes its ratios with it
"""

# Imports
import datetime as dt
from uuid import UUID
from sqlalchemy import select

from app.enums import MetricKind, Period
from app.models import Entry, EntryValue, Habit, Metric
from tests.helpers import add


def create(client, habit, **fields) -> dict:
    """Creates a metric in a habit → response body."""
    return client.post(f"/habits/{habit.id}/metrics", json=fields).json()


def test_create_typed_metrics(client, habit):
    """Number with its unit, duration without one."""
    km = create(client, habit, name="Distance", unit="km", kind="number")
    time = create(client, habit, name="Time", kind="duration")

    assert (km["unit"], time["unit"]) == ("km", None)
    assert [metric["name"] for metric in client.get(f"/habits/{habit.id}/metrics").json()] == ["Distance", "Time"]


def test_new_ratio_filled_in_for_past_sessions(client, db, habit):
    """Pace created after a 30-minute 10 km run → 180 s/km in that session."""
    time = add(db, Metric(habit_id=habit.id, name="Time", kind=MetricKind.DURATION))
    km = add(db, Metric(habit_id=habit.id, name="Km", unit="km", kind=MetricKind.NUMBER))
    add(db, Entry(habit_id=habit.id, date=dt.date(2026, 10, 5),
                  values=[EntryValue(metric_id=time.id, value=1800), EntryValue(metric_id=km.id, value=10)]))

    pace = create(client, habit, name="Pace", kind="ratio", operand_a_id=str(time.id), operand_b_id=str(km.id))

    paces = db.scalars(select(EntryValue.value).where(EntryValue.metric_id == UUID(pace["id"])))
    assert list(paces) == [180]


def test_ratio_operands_checked(client, db, user, habit):
    """Operand of another habit → 400, that does not exist → 404, a ratio → 400, missing → 422."""
    km = add(db, Metric(habit_id=habit.id, name="Km", unit="km", kind=MetricKind.NUMBER))
    time = add(db, Metric(habit_id=habit.id, name="Time", kind=MetricKind.DURATION))
    pace = add(db, Metric(habit_id=habit.id, name="Pace", kind=MetricKind.RATIO, operand_a_id=time.id, operand_b_id=km.id))
    other = add(db, Habit(user_id=user.id, name="Read", start_date=dt.date(2026, 1, 1), goal_target=1, goal_period=Period.DAILY))
    pages = add(db, Metric(habit_id=other.id, name="Pages", kind=MetricKind.NUMBER))

    def ratio(a, b):
        return client.post(f"/habits/{habit.id}/metrics", json={"name": "R", "kind": "ratio", "operand_a_id": a, "operand_b_id": b})

    assert ratio(str(time.id), str(pages.id)).status_code == 400
    assert ratio(str(time.id), "00000000-0000-0000-0000-000000000000").status_code == 404
    assert ratio(str(pace.id), str(km.id)).status_code == 400
    assert ratio(str(time.id), None).status_code == 422


def test_name_and_unit_editable_kind_and_habit_not(client, db, habit):
    """Rename and clear the unit; trying to change the kind or move it to another habit → 422."""
    km = add(db, Metric(habit_id=habit.id, name="Km", unit="km", kind=MetricKind.NUMBER))

    updated = client.patch(f"/metrics/{km.id}", json={"name": "Distance", "unit": None}).json()

    assert (updated["name"], updated["unit"]) == ("Distance", None)
    assert client.patch(f"/metrics/{km.id}", json={"kind": "duration"}).status_code == 422
    assert client.patch(f"/metrics/{km.id}", json={"habit_id": str(habit.id)}).status_code == 422


def test_delete_takes_its_ratios(client, db, habit):
    """Deleting time also deletes pace, which used it."""
    time = add(db, Metric(habit_id=habit.id, name="Time", kind=MetricKind.DURATION))
    km = add(db, Metric(habit_id=habit.id, name="Km", unit="km", kind=MetricKind.NUMBER))
    add(db, Metric(habit_id=habit.id, name="Pace", kind=MetricKind.RATIO, operand_a_id=time.id, operand_b_id=km.id))

    assert client.delete(f"/metrics/{time.id}").status_code == 204
    assert [metric["name"] for metric in client.get(f"/habits/{habit.id}/metrics").json()] == ["Km"]
