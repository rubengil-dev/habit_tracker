"""
Habits through the API:
    - Create with defaults; the v1 bugs on "active" (5 and 7) and the "at least 0" goal (4)
    - Start date: never in the future, never after a session
    - One habit with its streaks
    - Each user sees only their own habits
"""

# Imports
import datetime as dt

from app.enums import Period
from app.models import Entry, Habit, User
from tests.helpers import PASSWORD_HASH, TODAY, add

# A daily habit, as the front would send it
RUN = {"name": "Run", "goal_target": 1, "goal_period": "daily"}


# Create

def test_create_with_defaults(client):
    """Starts today, active, "at least" mode."""
    habit = client.post("/habits", json=RUN).json()

    assert (habit["start_date"], habit["active"], habit["goal_mode"]) == (str(TODAY), True, "min")


def test_create_inactive(client):
    """v1 bug 7: "active": false was ignored and the habit was always created active."""
    assert client.post("/habits", json=RUN | {"active": False}).json()["active"] is False


def test_goal_at_least_zero_rejected(client):
    """v1 bug 4: "at least 0" is always met; "at most 0" is a valid avoid goal."""
    assert client.post("/habits", json=RUN | {"goal_target": 0}).status_code == 422
    assert client.post("/habits", json=RUN | {"goal_target": 0, "goal_mode": "max"}).status_code == 201


def test_server_fields_cannot_be_sent(client):
    """Fields the API does not take are rejected, not silently ignored."""
    assert client.post("/habits", json=RUN | {"current_streak": 99}).status_code == 422


def test_duplicate_name_rejected(client):
    """Two habits of the same user cannot share a name."""
    client.post("/habits", json=RUN)
    assert client.post("/habits", json=RUN).status_code == 400


# Update

def test_null_rejected(client, habit):
    """v1 bug 5: {"active": null} used to be saved and broke every later GET."""
    assert client.patch(f"/habits/{habit.id}", json={"active": None}).status_code == 422
    assert client.get(f"/habits/{habit.id}").status_code == 200


def test_partial_update(client, habit):
    """Only the fields sent change."""
    updated = client.patch(f"/habits/{habit.id}", json={"name": "Running", "active": False}).json()

    assert (updated["name"], updated["active"], updated["goal_target"]) == ("Running", False, 1)


def test_start_date_not_in_the_future(client, habit):
    """Creating or moving a habit to start tomorrow → 400."""
    tomorrow = str(TODAY + dt.timedelta(days=1))

    assert client.post("/habits", json=RUN | {"start_date": tomorrow}).status_code == 400
    assert client.patch(f"/habits/{habit.id}", json={"start_date": tomorrow}).status_code == 400


def test_start_date_not_after_sessions(client, db, habit):
    """With a session on the 10th, the habit cannot start on the 11th; it can on the 10th."""
    add(db, Entry(habit_id=habit.id, date=dt.date(2026, 10, 10)))

    assert client.patch(f"/habits/{habit.id}", json={"start_date": "2026-10-11"}).status_code == 400
    assert client.patch(f"/habits/{habit.id}", json={"start_date": "2026-10-10"}).status_code == 200


# Read and delete

def test_habit_comes_with_streaks(client, db, habit):
    """Yesterday and the day before done, today pending: current 2, best 2."""
    add(db, Entry(habit_id=habit.id, date=TODAY - dt.timedelta(days=2)), Entry(habit_id=habit.id, date=TODAY - dt.timedelta(days=1)))

    detail = client.get(f"/habits/{habit.id}").json()

    assert (detail["current_streak"], detail["best_streak"]) == (2, 2)


def test_delete(client, habit):
    """204, and gone."""
    assert client.delete(f"/habits/{habit.id}").status_code == 204
    assert client.get(f"/habits/{habit.id}").status_code == 404


# Each user, their own

def test_other_users_habits_are_invisible(client, db, habit):
    """Someone else's habit: not listed, and 404 to read, change or delete it."""
    stranger = add(db, User(username="stranger", password_hash=PASSWORD_HASH))
    theirs = add(db, Habit(user_id=stranger.id, name="Secret", start_date=TODAY, goal_target=1, goal_period=Period.DAILY))

    assert [habit["name"] for habit in client.get("/habits").json()] == ["Run"]
    assert client.get(f"/habits/{theirs.id}").status_code == 404
    assert client.patch(f"/habits/{theirs.id}", json={"name": "Mine"}).status_code == 404
    assert client.delete(f"/habits/{theirs.id}").status_code == 404
