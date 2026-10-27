"""
Tags through the API:
    - Create and rename; names unique per habit
    - Before deleting: the badges that would go with it
    - Deleting: gone from sessions, its badges deleted, untagged-only badges recalculated
"""

# Imports
import datetime as dt

from app.enums import BadgeKind, TagRule
from app.models import Badge, BadgeTag, Entry, Tag
from tests.helpers import ASCENDING, add, count


def test_create_and_rename(client, habit):
    """Created, renamed; a repeated name in the same habit → 400."""
    rain = client.post(f"/habits/{habit.id}/tags", json={"name": "Rain"}).json()
    client.post(f"/habits/{habit.id}/tags", json={"name": "Tired"})

    assert client.patch(f"/tags/{rain['id']}", json={"name": "Storm"}).json()["name"] == "Storm"
    assert client.patch(f"/tags/{rain['id']}", json={"name": "Tired"}).status_code == 400


def test_badges_that_would_be_deleted(client, db, habit):
    """Required or excluded, both count: the warning lists them."""
    rain, tired = add(db, Tag(habit_id=habit.id, name="Rain")), add(db, Tag(habit_id=habit.id, name="Tired"))
    add(db, badge(habit, "In the rain", rain, TagRule.REQUIRED))
    add(db, badge(habit, "Fresh", tired, TagRule.EXCLUDED))

    assert [badge["name"] for badge in client.get(f"/tags/{rain.id}/badges").json()] == ["In the rain"]
    assert [badge["name"] for badge in client.get(f"/tags/{tired.id}/badges").json()] == ["Fresh"]


def test_delete_takes_its_badges_and_recalculates_the_rest(client, db, habit):
    """
    Deleting "rain":
        - Gone from the session, which stays
        - "In the rain" deleted; "No notes" (untagged only) now counts that session
    """
    rain = add(db, Tag(habit_id=habit.id, name="Rain"))
    add(db, Entry(habit_id=habit.id, date=dt.date(2026, 10, 5), tags=[rain]))
    add(db, badge(habit, "In the rain", rain, TagRule.REQUIRED))
    clean = add(db, Badge(habit_id=habit.id, name="No notes", kind=BadgeKind.HISTORIC, untagged_only=True, **ASCENDING))

    assert client.delete(f"/tags/{rain.id}").status_code == 204

    db.expire_all()
    assert [b.name for b in db.query(Badge)] == ["No notes"]
    assert count(db, Entry) == 1
    assert db.get(Badge, clean.id).current_value == 1


def badge(habit, name: str, tag: Tag, rule: TagRule) -> Badge:
    """Session-count badge with one tag rule."""
    return Badge(habit_id=habit.id, name=name, kind=BadgeKind.HISTORIC, tag_rules=[BadgeTag(tag_id=tag.id, rule=rule)], **ASCENDING)
