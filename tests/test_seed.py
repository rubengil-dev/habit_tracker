"""
Demo data script:
    - Builds the demo user with 5 habits, sessions and badges that pass the API's own rules
    - Running it again rebuilds the demo user, without touching anyone else
"""

# Imports
from sqlalchemy import select

from app.enums import TagRule, Tier
from app.models import Badge, Entry, Habit, User
from app.schemas import BadgeCreate, HabitCreate, check_as_whole
from scripts.seed_dev import USERNAME, seed
from tests.helpers import TODAY, count


def test_seed_builds_demo_user_with_history(db):
    """5 habits, months of sessions, ratios filled in and badges already earned."""
    demo = seed(db, "a long password", TODAY)
    db.commit()

    habits = db.scalars(select(Habit).where(Habit.user_id == demo.id)).all()
    badges = db.scalars(select(Badge).join(Habit).where(Habit.user_id == demo.id)).all()

    assert len(habits) == 5
    assert count(db, Entry) > 100
    assert any(badge.current_tier != Tier.LOCKED for badge in badges)


def test_seed_rows_pass_the_api_rules(db):
    """Rows are written straight to the database: each one must still be what the API would accept."""
    demo = seed(db, "a long password", TODAY)
    db.commit()

    for habit in db.scalars(select(Habit).where(Habit.user_id == demo.id)):
        check_as_whole(HabitCreate, habit, {})
        for badge in habit.badges:
            tag_ids = {
                "required_tag_ids": [rule.tag_id for rule in badge.tag_rules if rule.rule == TagRule.REQUIRED],
                "excluded_tag_ids": [rule.tag_id for rule in badge.tag_rules if rule.rule == TagRule.EXCLUDED],
            }
            check_as_whole(BadgeCreate, badge, {}, tag_ids)


def test_seed_twice_rebuilds_only_the_demo_user(db, user, habit):
    """Second run: same demo data, not doubled; the test user and their habit are still there."""
    seed(db, "a long password", TODAY)
    db.commit()
    entries_once = count(db, Entry)

    seed(db, "a long password", TODAY)
    db.commit()

    assert count(db, Entry) == entries_once
    assert db.scalars(select(User.username).order_by(User.username)).all() == [USERNAME, "tester"]
    assert db.get(Habit, habit.id) is not None
