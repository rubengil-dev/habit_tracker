"""
Daily view through the API:
    - Only active habits, with today's sessions, their goal so far and streaks
    - Avoid habits: a slip today shows at once
    - Badges that went up overnight are reported on opening, once
"""

# Imports
import datetime as dt

from app.enums import BadgeKind, GoalMode, Period
from app.models import Badge, Entry, Habit
from tests.helpers import ASCENDING, TODAY, add


def test_active_habits_with_their_day(client, db, user, habit):
    """Run done today and yesterday; an inactive habit is not listed."""
    add(db, Entry(habit_id=habit.id, date=TODAY), Entry(habit_id=habit.id, date=TODAY - dt.timedelta(days=1)))
    add(db, Habit(user_id=user.id, name="Old", active=False, start_date=TODAY, goal_target=1, goal_period=Period.DAILY))

    body = client.get("/today").json()
    run = body["habits"][0]

    assert body["date"] == str(TODAY)
    assert [row["habit"]["name"] for row in body["habits"]] == ["Run"]
    assert (run["today_count"], run["period_count"], run["goal_met"]) == (1, 1, True)
    assert (run["current_streak"], run["best_streak"]) == (2, 2)


def test_weekly_goal_so_far(client, db, user):
    """Three times a week, two sessions this week (Monday is today): not met yet."""
    gym = add(db, Habit(user_id=user.id, name="Gym", start_date=dt.date(2026, 10, 1), goal_target=3, goal_period=Period.WEEKLY))
    add(db, Entry(habit_id=gym.id, date=TODAY), Entry(habit_id=gym.id, date=TODAY))

    row = client.get("/today").json()["habits"][0]

    assert (row["period_count"], row["goal_met"]) == (2, False)


def test_avoid_slip_shows_at_once(client, db, user):
    """At most 0 a day, five clean days and a slip today: goal not met, streak 0, best 5."""
    smoke = add(db, Habit(user_id=user.id, name="Smoke", start_date=TODAY - dt.timedelta(days=5),
                          goal_target=0, goal_period=Period.DAILY, goal_mode=GoalMode.MAX))
    add(db, Entry(habit_id=smoke.id, date=TODAY))

    row = client.get("/today").json()["habits"][0]

    assert (row["goal_met"], row["current_streak"], row["best_streak"]) == (False, 0, 5)


def test_overnight_badges_reported_once(client, db, user, set_today):
    """Clean days badge at 2; ten days later, on opening, it is reported as gone to 12 (silver), and only once."""
    smoke = add(db, Habit(user_id=user.id, name="Smoke", start_date=TODAY - dt.timedelta(days=2),
                          goal_target=0, goal_period=Period.DAILY, goal_mode=GoalMode.MAX))
    add(db, Badge(habit_id=smoke.id, name="Clean days", kind=BadgeKind.CONSISTENCY,
                  period=Period.DAILY, target=0, mode=GoalMode.MAX, **ASCENDING))
    client.get("/today")

    set_today(TODAY + dt.timedelta(days=10))
    first = client.get("/today").json()["badge_changes"]
    second = client.get("/today").json()["badge_changes"]

    assert [(change["old_value"], change["new_value"], change["new_tier"]) for change in first] == [(2, 12, "silver")]
    assert second == []
