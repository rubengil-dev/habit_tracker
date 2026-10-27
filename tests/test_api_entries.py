"""
Sessions through the API:
    - Logged with values and tags → the session, badge changes and streaks, in one answer
    - Dates: today by default, never in the future, never before the habit starts
    - Values: metrics of the same habit, ratios calculated and never typed in, no NaN
    - Editing and deleting answer with the same report
"""

# Imports
import datetime as dt

from app.enums import MetricKind, Period
from app.models import Entry, Habit, Metric, Tag, User
from tests.helpers import PASSWORD_HASH, TODAY, add


def log(client, run, **body):
    """Logs a session in the running habit → response."""
    return client.post(f"/habits/{run.habit.id}/entries", json=body)


def run_values(run, time: float | None = 1800, km: float | None = 10) -> dict:
    """Values of a run, by metric id; None leaves one out."""
    values = {str(run.time.id): time, str(run.km.id): km}
    return {metric_id: value for metric_id, value in values.items() if value is not None}


# Logging

def test_log_reports_everything(client, run):
    """30 minutes, 10 km, in the rain → pace calculated, km badge to silver, a 1-day streak."""
    body = log(client, run, values=run_values(run), tag_ids=[str(run.rain.id)]).json()

    assert body["entry"]["date"] == str(TODAY)
    assert body["entry"]["values"][str(run.pace.id)] == 180
    assert body["entry"]["tag_ids"] == [str(run.rain.id)]
    assert body["badge_changes"] == [{
        "badge_id": str(run.km_badge.id), "name": "Km run",
        "old_value": None, "new_value": 10, "old_tier": "locked", "new_tier": "silver",
    }]
    assert (body["current_streak"], body["best_streak"]) == (1, 1)


def test_dates_checked(client, run):
    """Tomorrow → 400; before the habit starts (1/1/2026) → 400; yesterday, fine."""
    assert log(client, run, date=str(TODAY + dt.timedelta(days=1))).status_code == 400
    assert log(client, run, date="2025-12-31").status_code == 400
    assert log(client, run, date=str(TODAY - dt.timedelta(days=1))).status_code == 201


def test_values_checked(client, db, user, run):
    """Typing a ratio → 400; metric or tag of another habit → 400; unknown metric → 404; NaN → 422."""
    other = add(db, Habit(user_id=user.id, name="Read", start_date=dt.date(2026, 1, 1), goal_target=1, goal_period=Period.DAILY))
    pages = add(db, Metric(habit_id=other.id, name="Pages", kind=MetricKind.NUMBER))
    calm = add(db, Tag(habit_id=other.id, name="Calm"))

    assert log(client, run, values={str(run.pace.id): 180}).status_code == 400
    assert log(client, run, values={str(pages.id): 20}).status_code == 400
    assert log(client, run, tag_ids=[str(calm.id)]).status_code == 400
    assert log(client, run, values={"00000000-0000-0000-0000-000000000000": 1}).status_code == 404

    nan = f'{{"values": {{"{run.km.id}": NaN}}}}'
    response = client.post(f"/habits/{run.habit.id}/entries", content=nan, headers={"Content-Type": "application/json"})
    assert response.status_code == 422


def test_two_sessions_on_one_day(client, run):
    """Twice a day: the first session leaves today open, the second one meets it."""
    client.patch(f"/habits/{run.habit.id}", json={"goal_target": 2})

    assert log(client, run).json()["current_streak"] == 0
    assert log(client, run).json()["current_streak"] == 1


# Editing and deleting

def test_edit_replaces_values_and_tags(client, run):
    """Only 12 km sent: time and pace gone, tags cleared; the km badge reports 10 → 12."""
    entry_id = log(client, run, values=run_values(run), tag_ids=[str(run.rain.id)]).json()["entry"]["id"]

    body = client.patch(f"/entries/{entry_id}", json={"values": run_values(run, time=None, km=12), "tag_ids": []}).json()

    assert body["entry"]["values"] == {str(run.km.id): 12}
    assert body["entry"]["tag_ids"] == []
    assert [(change["old_value"], change["new_value"]) for change in body["badge_changes"]] == [(10, 12)]


def test_edit_date_checked(client, run):
    """A session cannot be moved to the future."""
    entry_id = log(client, run).json()["entry"]["id"]
    assert client.patch(f"/entries/{entry_id}", json={"date": str(TODAY + dt.timedelta(days=1))}).status_code == 400


def test_delete_reports_what_it_undid(client, run):
    """Deleting the only run: km badge back to locked, no streak, session gone."""
    entry_id = log(client, run, values=run_values(run)).json()["entry"]["id"]

    body = client.delete(f"/entries/{entry_id}").json()

    assert [(change["new_value"], change["new_tier"]) for change in body["badge_changes"]] == [(None, "locked")]
    assert (body["current_streak"], body["best_streak"]) == (0, 0)
    assert client.get(f"/entries/{entry_id}").status_code == 404


# Reading

def test_list_newest_first_and_between_dates(client, db, run):
    """Three sessions: newest first; from the 2nd to the 3rd, only those two."""
    for day in (1, 2, 3):
        add(db, Entry(habit_id=run.habit.id, date=dt.date(2026, 10, day)))

    every = client.get(f"/habits/{run.habit.id}/entries").json()
    some = client.get(f"/habits/{run.habit.id}/entries", params={"start": "2026-10-02", "end": "2026-10-03"}).json()

    assert [entry["date"] for entry in every] == ["2026-10-03", "2026-10-02", "2026-10-01"]
    assert [entry["date"] for entry in some] == ["2026-10-03", "2026-10-02"]


def test_other_users_sessions_invisible(client, db):
    """Someone else's habit and session: 404 to log in it, read, change or delete."""
    stranger = add(db, User(username="stranger", password_hash=PASSWORD_HASH))
    theirs = add(db, Habit(user_id=stranger.id, name="Secret", start_date=dt.date(2026, 1, 1), goal_target=1, goal_period=Period.DAILY))
    entry = add(db, Entry(habit_id=theirs.id, date=TODAY))

    assert client.post(f"/habits/{theirs.id}/entries", json={}).status_code == 404
    assert client.get(f"/entries/{entry.id}").status_code == 404
    assert client.patch(f"/entries/{entry.id}", json={"date": str(TODAY)}).status_code == 404
    assert client.delete(f"/entries/{entry.id}").status_code == 404
