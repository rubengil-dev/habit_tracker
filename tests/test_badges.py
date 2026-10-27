"""
Badge values:
    - One test per kind, in both directions where it applies
    - Tag filters: required, excluded and untagged only
    - Progress of consistency and streak badges
    - Recalculation saved in the database, reporting only what changed
"""

# Imports
import datetime as dt
from uuid import uuid4

from app.enums import BadgeKind, GoalMode, MetricKind, Period, TagRule, Tier
from app.models import Badge, BadgeTag, Entry, EntryValue, Metric, Tag
from app.services.badges import badge_progress, badge_value, recalculate_badges
from app.services.ratios import backfill_ratio
from tests.helpers import ASCENDING, add, facts, make_badge

# Monday
TODAY = dt.date(2026, 10, 26)
START = dt.date(2026, 10, 1)

# Metrics and tags of a run
KM, PACE = uuid4(), uuid4()
RAIN, TIRED, PAIN = uuid4(), uuid4(), uuid4()

# Four runs: km and pace (seconds per km), and one without values
RUNS = [
    facts(dt.date(2026, 10, 5),  {KM: 5,    PACE: 330}),
    facts(dt.date(2026, 10, 12), {KM: 10,   PACE: 310}, tags=(RAIN,)),
    facts(dt.date(2026, 10, 19), {KM: 12.5, PACE: 295}, tags=(RAIN, TIRED)),
    facts(dt.date(2026, 10, 20)),
]


def value_of(badge: Badge, history: list = RUNS) -> float | None:
    """Value of a badge over a history, today."""
    return badge_value(badge, history, START, TODAY)


def rules(**tags) -> list[BadgeTag]:
    """Tag rules of an unsaved badge: required=[...], excluded=[...]."""
    return [BadgeTag(tag_id=tag_id, rule=TagRule(rule)) for rule, ids in tags.items() for tag_id in ids]


# One value per kind

def test_historic_sum_of_metric():
    """Km run: sessions without km add nothing."""
    assert value_of(make_badge(kind=BadgeKind.HISTORIC, metric_id=KM)) == 27.5


def test_historic_number_of_sessions():
    """Without a metric it counts sessions, the one without values too ("I did it")."""
    assert value_of(make_badge(kind=BadgeKind.HISTORIC)) == 4


def test_historic_without_values_is_none():
    """Nothing to add yet → None, so the badge stays locked."""
    assert value_of(make_badge(kind=BadgeKind.HISTORIC, metric_id=KM), []) is None


def test_record_both_directions():
    """Longest run, and fastest pace (lowest)."""
    assert value_of(make_badge(kind=BadgeKind.RECORD, metric_id=KM)) == 12.5
    assert value_of(make_badge(kind=BadgeKind.RECORD, metric_id=PACE, higher_is_better=False)) == 295


def test_record_without_sessions_is_none():
    """v1 bug 3: no sessions used to give 0, which is a perfect "lower is better" record."""
    assert value_of(make_badge(kind=BadgeKind.RECORD, metric_id=PACE, higher_is_better=False), []) is None


def test_objective_both_directions():
    """Runs of 10 km or more, and runs at 5'10'' per km or faster."""
    assert value_of(make_badge(kind=BadgeKind.OBJECTIVE, metric_id=KM, threshold=10)) == 2
    assert value_of(make_badge(kind=BadgeKind.OBJECTIVE, metric_id=PACE, threshold=310, higher_is_better=False)) == 2


def test_consistency_counts_met_periods():
    """Once a week: weeks of the 5th, 12th and 19th met; the current one, with no run yet, does not count."""
    badge = make_badge(kind=BadgeKind.CONSISTENCY, period=Period.WEEKLY, target=1, mode=GoalMode.MIN)
    assert value_of(badge) == 3


def test_consistency_avoid_counts_closed_clean_periods():
    """At most 0 a day, from the 1st: 25 closed days, 4 of them with a session; today does not count yet."""
    badge = make_badge(kind=BadgeKind.CONSISTENCY, period=Period.DAILY, target=0, mode=GoalMode.MAX)
    assert value_of(badge) == 21


def test_streak_value_is_best_streak():
    """Its tier comes from the best streak; the current one is shown as progress."""
    badge = make_badge(kind=BadgeKind.STREAK, period=Period.WEEKLY, target=1, mode=GoalMode.MIN)
    history = RUNS + [facts(dt.date(2026, 10, 2))]           # Week of the 28th of September too

    assert value_of(badge, history) == 4
    assert badge_progress(badge, history, START, TODAY).current_streak == 4


def test_streak_value_survives_a_break():
    """Best streak 4 weeks; after a missed week the current one drops, the badge value does not."""
    badge = make_badge(kind=BadgeKind.STREAK, period=Period.WEEKLY, target=1, mode=GoalMode.MIN)
    history = RUNS + [facts(dt.date(2026, 10, 2))]
    two_weeks_later = dt.date(2026, 11, 9)

    assert badge_value(badge, history, START, two_weeks_later) == 4
    assert badge_progress(badge, history, START, two_weeks_later).current_streak == 0


def test_streak_badge_in_avoid_mode():
    """At most 0 a day: best clean run is 6 days (6th to 11th, and 13th to 18th); the current one, 5 days."""
    badge = make_badge(kind=BadgeKind.STREAK, period=Period.DAILY, target=0, mode=GoalMode.MAX)

    assert value_of(badge) == 6
    assert badge_progress(badge, RUNS, START, TODAY).current_streak == 5


def test_consistency_with_a_bar():
    """Weeks with a run of 10 km or more."""
    badge = make_badge(
        kind=BadgeKind.CONSISTENCY, metric_id=KM, threshold=10,
        period=Period.WEEKLY, target=1, mode=GoalMode.MIN,
    )
    assert value_of(badge) == 2


# Tag filters

def test_required_tags_must_all_be_there():
    """Rain and tired together: only the run of the 19th."""
    badge = make_badge(kind=BadgeKind.HISTORIC, tag_rules=rules(required=[RAIN, TIRED]))
    assert value_of(badge) == 1


def test_excluded_tags_must_all_be_missing():
    """Without tiredness: three sessions."""
    badge = make_badge(kind=BadgeKind.HISTORIC, tag_rules=rules(excluded=[TIRED]))
    assert value_of(badge) == 3


def test_required_and_excluded_together():
    """In the rain but not tired: only the run of the 12th."""
    badge = make_badge(kind=BadgeKind.HISTORIC, metric_id=KM, tag_rules=rules(required=[RAIN], excluded=[TIRED]))
    assert value_of(badge) == 10


def test_untagged_only():
    """Sessions without any tag: the 5th and the 20th."""
    badge = make_badge(kind=BadgeKind.HISTORIC, untagged_only=True)
    assert value_of(badge) == 2


# Progress

def test_consistency_progress_this_period():
    """Three times a week: two runs so far this week → 2/3."""
    badge = make_badge(kind=BadgeKind.CONSISTENCY, period=Period.WEEKLY, target=3, mode=GoalMode.MIN)
    history = RUNS + [facts(TODAY), facts(TODAY)]
    progress = badge_progress(badge, history, START, TODAY)

    assert (progress.period_count, progress.target, progress.current_streak) == (2, 3, None)


def test_avoid_progress_shows_what_is_over():
    """At most 0 a day, one session today → 1/0: the front can show the slip."""
    badge = make_badge(kind=BadgeKind.CONSISTENCY, period=Period.DAILY, target=0, mode=GoalMode.MAX)
    progress = badge_progress(badge, RUNS + [facts(TODAY)], START, TODAY)

    assert (progress.period_count, progress.target) == (1, 0)


def test_no_progress_for_other_kinds():
    """Only consistency and streak badges have a period."""
    assert badge_progress(make_badge(kind=BadgeKind.HISTORIC), RUNS, START, TODAY) is None


# Recalculation in the database

def test_recalculation_saves_and_reports_changes(db, habit):
    """New session → badge saved with its value and tier, reported once; nothing changes the second time."""
    km = add(db, Metric(habit_id=habit.id, name="Km", unit="km", kind=MetricKind.NUMBER))
    badge = add(db, Badge(habit_id=habit.id, metric_id=km.id, name="Km run", kind=BadgeKind.HISTORIC, **ASCENDING))
    add(db, Entry(habit_id=habit.id, date=dt.date(2026, 10, 5), values=[EntryValue(metric_id=km.id, value=7)]))

    changes = recalculate_badges(db, habit, TODAY)

    assert [(change.badge.id, change.old_value, change.old_tier) for change in changes] == [(badge.id, None, Tier.LOCKED)]
    assert (badge.current_value, badge.current_tier) == (7, Tier.BRONZE)
    assert recalculate_badges(db, habit, TODAY) == []


def test_recalculation_after_deleting_every_session(db, habit):
    """No sessions left → a record goes back to locked, it does not keep its old value."""
    km = add(db, Metric(habit_id=habit.id, name="Km", unit="km", kind=MetricKind.NUMBER))
    badge = add(db, Badge(habit_id=habit.id, metric_id=km.id, name="Longest", kind=BadgeKind.RECORD, **ASCENDING))
    entry = add(db, Entry(habit_id=habit.id, date=dt.date(2026, 10, 5), values=[EntryValue(metric_id=km.id, value=7)]))
    recalculate_badges(db, habit, TODAY)

    db.delete(entry)
    recalculate_badges(db, habit, TODAY)

    assert (badge.current_value, badge.current_tier) == (None, Tier.LOCKED)


def test_recalculation_with_tags_and_ratio_from_the_database(db, habit):
    """Best pace in the rain: tag rules and ratio values read back from their tables."""
    time = add(db, Metric(habit_id=habit.id, name="Time", kind=MetricKind.DURATION))
    km = add(db, Metric(habit_id=habit.id, name="Km", unit="km", kind=MetricKind.NUMBER))
    rain = add(db, Tag(habit_id=habit.id, name="Rain"))
    add(db,
        Entry(habit_id=habit.id, date=dt.date(2026, 10, 5), tags=[rain], values=[EntryValue(metric_id=time.id, value=1500), EntryValue(metric_id=km.id, value=5)]),
        Entry(habit_id=habit.id, date=dt.date(2026, 10, 6), values=[EntryValue(metric_id=time.id, value=2700), EntryValue(metric_id=km.id, value=10)]),
        Entry(habit_id=habit.id, date=dt.date(2026, 10, 7), tags=[rain], values=[EntryValue(metric_id=time.id, value=1680), EntryValue(metric_id=km.id, value=6)]),
    )
    pace = Metric(habit_id=habit.id, name="Pace", kind=MetricKind.RATIO, operand_a_id=time.id, operand_b_id=km.id)
    db.add(pace)
    backfill_ratio(db, pace)
    badge = add(db, Badge(
        habit_id=habit.id, metric_id=pace.id, name="Rainy pace", kind=BadgeKind.RECORD, higher_is_better=False,
        unlocked=400, bronze=360, silver=330, gold=300, diamond=270,
        tag_rules=[BadgeTag(tag_id=rain.id, rule=TagRule.REQUIRED)],
    ))
    db.expire_all()

    recalculate_badges(db, habit, TODAY)

    assert (badge.current_value, badge.current_tier) == (280, Tier.GOLD)
