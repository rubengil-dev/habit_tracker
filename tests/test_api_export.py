"""
Export through the API: everything of the user, nothing of anyone else, as a dated file.
"""

# Imports
import datetime as dt

from app.enums import Period, TagRule
from app.models import BadgeTag, Entry, EntryValue, Habit, User
from tests.helpers import PASSWORD_HASH, TODAY, add


def test_export_everything_and_only_mine(client, db, run):
    """User, habit with its metrics, tags, sessions (pace included) and badges; the stranger's habit left out."""
    add(db, Entry(habit_id=run.habit.id, date=TODAY, tags=[run.rain], values=[
        EntryValue(metric_id=run.time.id, value=1800), EntryValue(metric_id=run.km.id, value=10),
        EntryValue(metric_id=run.pace.id, value=180),
    ]))
    add(db, BadgeTag(badge_id=run.km_badge.id, tag_id=run.rain.id, rule=TagRule.REQUIRED))
    stranger = add(db, User(username="stranger", password_hash=PASSWORD_HASH))
    add(db, Habit(user_id=stranger.id, name="Secret", start_date=dt.date(2026, 1, 1), goal_target=1, goal_period=Period.DAILY))

    response = client.get("/export")
    body = response.json()
    habit = body["habits"][0]

    assert response.headers["Content-Disposition"] == f'attachment; filename="habit-tracker-{TODAY}.json"'
    assert (body["format_version"], body["user"]["username"]) == (1, "tester")
    assert [habit["name"] for habit in body["habits"]] == ["Run"]
    assert [metric["name"] for metric in habit["metrics"]] == ["Time", "Km", "Pace"]
    assert [tag["name"] for tag in habit["tags"]] == ["Rain"]
    assert habit["entries"][0]["values"][str(run.pace.id)] == 180
    assert habit["badges"][0]["required_tag_ids"] == [str(run.rain.id)]
