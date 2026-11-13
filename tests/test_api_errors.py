"""
Error answers: always {"detail", "code"}, so the front can pick its message by code:
    - The app's own errors, the framework's (unknown path), validation and database rules
"""

# Imports
import datetime as dt

from app.errors import integrity_answer
from tests.helpers import TODAY


def test_not_logged_in_carries_its_code(anon_client):
    """Without a session: 401 with its code."""
    assert anon_client.get("/habits").json() == {"detail": "Not logged in", "code": "not_logged_in"}


def test_app_errors_carry_their_code(client, run):
    """Not found and a rule of the app."""
    tomorrow = str(TODAY + dt.timedelta(days=1))

    assert client.get("/habits/00000000-0000-0000-0000-000000000000").json()["code"] == "not_found"
    assert client.post(f"/habits/{run.habit.id}/entries", json={"date": tomorrow}).json()["code"] == "future_date"


def test_framework_and_validation_errors_carry_a_code(client):
    """Unknown path → not_found; a body that breaks a rule → validation_error, with where and why."""
    unknown = client.get("/nowhere")
    invalid = client.post("/habits", json={"name": ""}).json()

    assert (unknown.status_code, unknown.json()["code"]) == (404, "not_found")
    assert invalid["code"] == "validation_error"
    assert {"type", "loc", "msg"} <= invalid["detail"][0].keys()


def test_login_lockout_keeps_retry_after(anon_client, user):
    """The coded 429 still says how long to wait."""
    for _ in range(5):
        anon_client.post("/auth/login", json={"username": "tester", "password": "not it"})
    response = anon_client.post("/auth/login", json={"username": "tester", "password": "not it"})

    assert response.json()["code"] == "login_locked"
    assert "Retry-After" in response.headers


def test_database_rules_never_echo_the_database_text():
    """SQLite and Postgres messages → the same coded answer, without values from the database."""
    sqlite_unique = "UNIQUE constraint failed: habits.user_id, habits.name"
    postgres_unique = 'duplicate key value violates unique constraint "uq_habits_user_id_name"\nDETAIL: Key (name)=(Run)'
    postgres_check = 'new row for relation "habits" violates check constraint "ck_habits_goal_target_valid"'

    assert integrity_answer(sqlite_unique) == integrity_answer(postgres_unique) == (409, "duplicate_name", "That name is already in use")
    assert integrity_answer(postgres_check) == (400, "integrity_error", "The change breaks a database rule")
