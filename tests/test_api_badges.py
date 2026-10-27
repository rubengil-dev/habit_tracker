"""
Badges through the API:
    - A new badge takes the habit's history at once
    - Rules per kind, tag filters and tier order (422), checked again as a whole on every edit
    - Reading recalculates: an avoid badge grows with the days, with no new sessions
    - Progress, suggested thresholds, and each user sees only their own
"""

# Imports
import datetime as dt
import pytest

from app.enums import BadgeKind, GoalMode, MetricKind, Period
from app.models import Badge, Entry, EntryValue, Habit, Metric, User
from tests.helpers import ASCENDING, PASSWORD_HASH, TODAY, add

# Payloads that break a rule, each one built from the running habit
INVALID = {
    "record without metric":            lambda run: dict(kind="record"),
    "objective without threshold":      lambda run: dict(kind="objective", metric_id=str(run.km.id)),
    "consistency without its goal":     lambda run: dict(kind="consistency", period="weekly"),
    "historic with a period":           lambda run: dict(kind="historic", period="weekly", target=1, mode="min"),
    "historic with a threshold":        lambda run: dict(kind="historic", metric_id=str(run.km.id), threshold=10),
    "consistency metric without bar":   lambda run: dict(kind="consistency", metric_id=str(run.km.id), period="weekly", target=1, mode="min"),
    "session count going down":         lambda run: dict(kind="historic", higher_is_better=False, **reversed_tiers()),
    "at least 0":                       lambda run: dict(kind="streak", period="daily", target=0, mode="min"),
    "untagged only with a tag":         lambda run: dict(kind="historic", untagged_only=True, required_tag_ids=[str(run.rain.id)]),
    "tag required and excluded":        lambda run: dict(kind="historic", required_tag_ids=[str(run.rain.id)], excluded_tag_ids=[str(run.rain.id)]),
    "tiers going down":                 lambda run: dict(kind="historic", **reversed_tiers()),
    "lower is better, tiers going up":  lambda run: dict(kind="record", metric_id=str(run.km.id), higher_is_better=False),
    "value set by the client":          lambda run: dict(kind="historic", current_value=1000),
}


def payload(**fields) -> dict:
    """New badge body: a name and tiers going up, plus the given fields."""
    return {"name": "Badge"} | ASCENDING | fields


def reversed_tiers() -> dict:
    """Tiers going down: 100 → 1."""
    return dict(zip(ASCENDING, reversed(ASCENDING.values())))


def create(client, habit, **fields):
    """Creates a badge in a habit → response."""
    return client.post(f"/habits/{habit.id}/badges", json=payload(**fields))


# Creating

def test_new_badge_takes_history(client, db, run):
    """Two runs of 5 and 7 km already logged → the new badge starts at 12, silver."""
    for day, km in ((5, 5), (6, 7)):
        add(db, Entry(habit_id=run.habit.id, date=dt.date(2026, 10, day), values=[EntryValue(metric_id=run.km.id, value=km)]))

    badge = create(client, run.habit, kind="historic", metric_id=str(run.km.id)).json()

    assert (badge["current_value"], badge["current_tier"]) == (12, "silver")


@pytest.mark.parametrize("make", INVALID.values(), ids=INVALID.keys())
def test_invalid_badges_rejected(client, run, make):
    """Each broken rule → 422."""
    assert create(client, run.habit, **make(run)).status_code == 422


def test_metric_and_tags_of_the_same_habit(client, db, user, run):
    """Metric of another habit → 400; a tag that does not exist → 404."""
    other = add(db, Habit(user_id=user.id, name="Read", start_date=dt.date(2026, 1, 1), goal_target=1, goal_period=Period.DAILY))
    pages = add(db, Metric(habit_id=other.id, name="Pages", kind=MetricKind.NUMBER))

    assert create(client, run.habit, kind="record", metric_id=str(pages.id)).status_code == 400
    assert create(client, run.habit, kind="historic", required_tag_ids=["00000000-0000-0000-0000-000000000000"]).status_code == 404


# Editing

def test_edit_thresholds_recalculates(client, db, run):
    """12 km logged; diamond lowered to 12 → the badge is diamond at once."""
    add(db, Entry(habit_id=run.habit.id, date=dt.date(2026, 10, 5), values=[EntryValue(metric_id=run.km.id, value=12)]))
    new_tiers = dict(unlocked=1, bronze=2, silver=3, gold=4, diamond=12)

    badge = client.patch(f"/badges/{run.km_badge.id}", json=new_tiers).json()

    assert badge["current_tier"] == "diamond"


def test_edit_checked_as_a_whole(client, db, run):
    """Bronze above silver → 422; untagged only on a badge that requires a tag → 422; kind → 422."""
    tagged = create(client, run.habit, kind="historic", required_tag_ids=[str(run.rain.id)]).json()

    assert client.patch(f"/badges/{run.km_badge.id}", json={"bronze": 20}).status_code == 422
    assert client.patch(f"/badges/{tagged['id']}", json={"untagged_only": True}).status_code == 422
    assert client.patch(f"/badges/{run.km_badge.id}", json={"kind": "record"}).status_code == 422


def test_edit_tag_rules(client, run):
    """Rain required, then excluded instead."""
    badge_id = create(client, run.habit, kind="historic", required_tag_ids=[str(run.rain.id)]).json()["id"]

    badge = client.patch(f"/badges/{badge_id}", json={"required_tag_ids": [], "excluded_tag_ids": [str(run.rain.id)]}).json()

    assert (badge["required_tag_ids"], badge["excluded_tag_ids"]) == ([], [str(run.rain.id)])


# Reading

def test_avoid_badge_grows_with_the_days(client, db, user, set_today):
    """"Days without smoking": 2 clean days → unlocked; ten days later, with no sessions, 12 → silver."""
    smoke = add(db, Habit(user_id=user.id, name="Smoke", start_date=TODAY - dt.timedelta(days=2),
                          goal_target=0, goal_period=Period.DAILY, goal_mode=GoalMode.MAX))
    add(db, Badge(habit_id=smoke.id, name="Clean days", kind=BadgeKind.CONSISTENCY,
                  period=Period.DAILY, target=0, mode=GoalMode.MAX, **ASCENDING))

    before = client.get(f"/habits/{smoke.id}/badges").json()[0]
    set_today(TODAY + dt.timedelta(days=10))
    after = client.get(f"/habits/{smoke.id}/badges").json()[0]

    assert (before["current_value"], before["current_tier"]) == (2, "unlocked")
    assert (after["current_value"], after["current_tier"]) == (12, "silver")


def test_progress_of_periodic_badges(client, db, run):
    """Three times a week, one run this week → 1/3; a streak badge also shows its current streak."""
    add(db, Entry(habit_id=run.habit.id, date=TODAY))
    week = dict(period="weekly", target=3, mode="min")

    consistency = create(client, run.habit, kind="consistency", **week).json()
    streak = create(client, run.habit, kind="streak", **week).json()

    assert consistency["progress"] == {"period_count": 1, "target": 3, "current_streak": None}
    assert streak["progress"] == {"period_count": 1, "target": 3, "current_streak": 0}
    assert client.get(f"/badges/{run.km_badge.id}").json()["progress"] is None


def test_all_badges_only_mine(client, db, run):
    """Badges of every habit of mine; someone else's, neither listed nor readable."""
    stranger = add(db, User(username="stranger", password_hash=PASSWORD_HASH))
    theirs = add(db, Habit(user_id=stranger.id, name="Secret", start_date=TODAY, goal_target=1, goal_period=Period.DAILY))
    their_badge = add(db, Badge(habit_id=theirs.id, name="Secret badge", kind=BadgeKind.HISTORIC, **ASCENDING))

    assert [badge["name"] for badge in client.get("/badges").json()] == ["Km run"]
    assert client.get(f"/badges/{their_badge.id}").status_code == 404


def test_suggested_tiers(client):
    """100 → 100,000 km: friendly numbers; a 0 end → 422."""
    assert client.get("/badges/suggest-tiers", params={"first": 100, "diamond": 100000}).json() == {"tiers": [100, 500, 3000, 20000, 100000]}
    assert client.get("/badges/suggest-tiers", params={"first": 0, "diamond": 10}).status_code == 422


def test_delete(client, run):
    """204, and gone."""
    assert client.delete(f"/badges/{run.km_badge.id}").status_code == 204
    assert client.get(f"/badges/{run.km_badge.id}").status_code == 404
