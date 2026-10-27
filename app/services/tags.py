"""
Tag deletion:
    - Badges that use the tag (required or excluded) go with it, so none silently changes meaning
    - The rest of the habit's badges are recalculated: untagged-only ones may now count more sessions
"""

# Imports
import datetime as dt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Badge, BadgeTag, Habit, Tag
from app.services.badges import recalculate_badges


def delete_tag(db: Session, tag: Tag, today: dt.date):
    """Tag deleted along with the badges that use it; the habit's other badges recalculated."""
    habit = db.get(Habit, tag.habit_id)

    for badge in badges_using(db, tag):
        db.delete(badge)
    db.delete(tag)
    db.flush()

    recalculate_badges(db, habit, today)


def badges_using(db: Session, tag: Tag) -> list[Badge]:
    """Badges with a rule on the tag: the ones deleting it would delete."""
    query = select(Badge).join(BadgeTag).where(BadgeTag.tag_id == tag.id).order_by(Badge.created_at)
    return list(db.scalars(query))
