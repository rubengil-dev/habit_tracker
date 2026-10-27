"""
Database rules, checked straight on the tables (no API):
    - Required values, enums and value ranges
    - Badge rules per kind and tiers order
    - Unique names per owner
    - Cascade deletion
"""

# Imports
import datetime as dt
import pytest
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError

from app.enums import BadgeKind, GoalMode, MetricKind, Period, TagRule
from app.models import Badge, BadgeTag, Entry, EntryValue, Habit, Metric, Tag, User, entry_tags
from tests.helpers import ASCENDING, add, assert_rejected, count

# Thresholds
DESCENDING = dict(unlocked=400, bronze=360, silver=330, gold=300, diamond=270)       # e.g. pace in seconds per km
DAY = dt.date(2026, 1, 1)


# Required values, enums and ranges

def test_booleans_reject_null(db, user):
    """
    v1 bug 5: a null boolean used to be saved and broke every later GET:
        - Sent straight to the database, because the ORM swaps None for the default
    """
    row = dict(user_id=user.id, name="Gym", active=None, start_date=DAY, goal_target=1, goal_period="weekly")

    with pytest.raises(IntegrityError):
        db.execute(insert(Habit.__table__).values(**row))
    db.rollback()


def test_goal_at_least_zero_rejected(db, user):
    """v1 bug 4: "at least 0 times" is always met, so it is not a goal."""
    assert_rejected(db, Habit(user_id=user.id, name="Gym", start_date=DAY, goal_target=0, goal_period=Period.WEEKLY))
    assert_rejected(db, Habit(user_id=user.id, name="Gym", start_date=DAY, goal_target=-1, goal_period=Period.WEEKLY, goal_mode=GoalMode.MAX))


def test_goal_at_most_zero_accepted(db, user):
    """Avoid mode: "at most 0 times a day" is a valid goal."""
    add(db, Habit(user_id=user.id, name="Smoke", start_date=DAY, goal_target=0, goal_period=Period.DAILY, goal_mode=GoalMode.MAX))
    assert count(db, Habit) == 1


def test_enum_values_checked_by_database(db, user):
    """A value outside the enum is stopped by the database itself, not only by the API."""
    assert_rejected(db, Habit(user_id=user.id, name="Gym", start_date=DAY, goal_target=1, goal_period="fortnightly"))


def test_datetimes_come_back_with_timezone(db, user):
    """SQLite returns datetimes without timezone: UTCDateTime gives them back in UTC, like Postgres."""
    db.expire_all()
    assert db.get(User, user.id).created_at.utcoffset() == dt.timedelta(0)


def test_ratio_needs_two_different_operands(db, habit):
    """A ratio needs operands A and B, different; a typed-in metric has none."""
    distance = add(db, Metric(habit_id=habit.id, name="Distance", unit="km", kind=MetricKind.NUMBER))
    time = add(db, Metric(habit_id=habit.id, name="Time", kind=MetricKind.DURATION))

    assert_rejected(db, Metric(habit_id=habit.id, name="Pace", kind=MetricKind.RATIO, operand_a_id=time.id))
    assert_rejected(db, Metric(habit_id=habit.id, name="Pace", kind=MetricKind.RATIO, operand_a_id=time.id, operand_b_id=time.id))
    assert_rejected(db, Metric(habit_id=habit.id, name="Pace", kind=MetricKind.NUMBER, operand_a_id=time.id, operand_b_id=distance.id))

    add(db, Metric(habit_id=habit.id, name="Pace", kind=MetricKind.RATIO, operand_a_id=time.id, operand_b_id=distance.id))
    assert count(db, Metric) == 3


# Badges

def test_tiers_order(db, habit):
    """Counts always go up; historic and record go down only when lower is better."""
    pace = add(db, Metric(habit_id=habit.id, name="Pace", kind=MetricKind.NUMBER))

    # Valid
    add(db, Badge(habit_id=habit.id, name="Sessions", kind=BadgeKind.HISTORIC, **ASCENDING))
    add(db, Badge(habit_id=habit.id, metric_id=pace.id, name="Best pace", kind=BadgeKind.RECORD, higher_is_better=False, **DESCENDING))

    # Lower is better, but tiers going up
    assert_rejected(db, Badge(habit_id=habit.id, metric_id=pace.id, name="Bad", kind=BadgeKind.RECORD, higher_is_better=False, **ASCENDING))

    # A count with tiers going down, even if lower is better for its bar
    assert_rejected(db, Badge(
        habit_id=habit.id, metric_id=pace.id, name="Bad", kind=BadgeKind.OBJECTIVE,
        higher_is_better=False, threshold=300, **DESCENDING,
    ))
    assert count(db, Badge) == 2


def test_badge_needs_its_fields(db, habit):
    """Each kind needs its fields: record a metric, objective a bar, consistency and streak a period goal."""
    distance = add(db, Metric(habit_id=habit.id, name="Distance", unit="km", kind=MetricKind.NUMBER))

    assert_rejected(db, Badge(habit_id=habit.id, name="Bad", kind=BadgeKind.RECORD, **ASCENDING))
    assert_rejected(db, Badge(habit_id=habit.id, metric_id=distance.id, name="Bad", kind=BadgeKind.OBJECTIVE, **ASCENDING))
    assert_rejected(db, Badge(habit_id=habit.id, name="Bad", kind=BadgeKind.HISTORIC, threshold=10, **ASCENDING))
    assert_rejected(db, Badge(habit_id=habit.id, name="Bad", kind=BadgeKind.CONSISTENCY, period=Period.WEEKLY, **ASCENDING))
    assert_rejected(db, Badge(
        habit_id=habit.id, name="Bad", kind=BadgeKind.STREAK,
        period=Period.WEEKLY, target=0, mode=GoalMode.MIN, **ASCENDING,
    ))

    # Avoid mode: "at most 0 a day", 30 days in a row
    add(db, Badge(
        habit_id=habit.id, name="Clean", kind=BadgeKind.STREAK,
        period=Period.DAILY, target=0, mode=GoalMode.MAX, **ASCENDING,
    ))
    assert count(db, Badge) == 1


def test_tag_cannot_be_required_and_excluded(db, habit):
    """One rule per tag and badge."""
    rain_id = add(db, Tag(habit_id=habit.id, name="Rain")).id
    badge_id = add(db, Badge(habit_id=habit.id, name="Rainy runs", kind=BadgeKind.HISTORIC, **ASCENDING)).id

    add(db, BadgeTag(badge_id=badge_id, tag_id=rain_id, rule=TagRule.REQUIRED))
    db.expunge_all()            # Forget the saved rule, so the database is the one that refuses
    assert_rejected(db, BadgeTag(badge_id=badge_id, tag_id=rain_id, rule=TagRule.EXCLUDED))


# Unique names

def test_names_unique_per_owner(db, user, habit):
    """Habit names are unique per user, metric and tag names per habit."""
    other_user = add(db, User(username="other", password_hash="not-a-real-hash"))
    other_habit = add(db, Habit(user_id=user.id, name="Read", start_date=DAY, goal_target=1, goal_period=Period.DAILY))

    assert_rejected(db, Habit(user_id=user.id, name="Run", start_date=DAY, goal_target=1, goal_period=Period.DAILY))
    add(db, Habit(user_id=other_user.id, name="Run", start_date=DAY, goal_target=1, goal_period=Period.DAILY))

    add(db, Tag(habit_id=habit.id, name="Tired"))
    assert_rejected(db, Tag(habit_id=habit.id, name="Tired"))
    add(db, Tag(habit_id=other_habit.id, name="Tired"))
    assert count(db, Tag) == 2


# Cascade deletion

def test_deleting_habit_deletes_everything(db, habit):
    """Habit → metrics, tags, sessions with their values and tags, badges with their tag rules."""
    distance, entry, rain = build_history(db, habit)
    add(db, Badge(habit_id=habit.id, metric_id=distance.id, name="Km", kind=BadgeKind.HISTORIC, **ASCENDING))
    badge = add(db, Badge(habit_id=habit.id, name="Rainy runs", kind=BadgeKind.HISTORIC, **ASCENDING))
    add(db, BadgeTag(badge_id=badge.id, tag_id=rain.id, rule=TagRule.REQUIRED))

    db.delete(habit)
    db.commit()

    for table in (Metric, Tag, Entry, EntryValue, entry_tags, Badge, BadgeTag):
        assert count(db, table) == 0


def test_deleting_metric_deletes_its_ratios(db, habit):
    """Metric → its values, the ratios that use it and their values, and the badges of all of them."""
    distance, entry, rain = build_history(db, habit)
    time = add(db, Metric(habit_id=habit.id, name="Time", kind=MetricKind.DURATION))
    pace = add(db, Metric(habit_id=habit.id, name="Pace", kind=MetricKind.RATIO, operand_a_id=time.id, operand_b_id=distance.id))
    add(db, EntryValue(entry_id=entry.id, metric_id=time.id, value=1800), EntryValue(entry_id=entry.id, metric_id=pace.id, value=180))
    add(db, Badge(habit_id=habit.id, metric_id=pace.id, name="Best pace", kind=BadgeKind.RECORD, higher_is_better=False, **DESCENDING))

    db.delete(time)
    db.commit()

    assert [metric.name for metric in db.query(Metric)] == ["Distance"]
    assert count(db, EntryValue) == 1
    assert count(db, Badge) == 0
    assert count(db, Entry) == 1


def test_deleting_tag_removes_it_from_sessions(db, habit):
    """Tag → gone from every session; the sessions stay."""
    distance, entry, rain = build_history(db, habit)

    db.delete(rain)
    db.commit()

    assert count(db, entry_tags) == 0
    assert count(db, Entry) == 1


def build_history(db, habit):
    """One session with a distance and the "Rain" tag → (distance, session, tag)."""
    distance = add(db, Metric(habit_id=habit.id, name="Distance", unit="km", kind=MetricKind.NUMBER))
    rain = add(db, Tag(habit_id=habit.id, name="Rain"))
    entry = add(db, Entry(habit_id=habit.id, date=DAY, values=[EntryValue(metric_id=distance.id, value=10)], tags=[rain]))
    return distance, entry, rain