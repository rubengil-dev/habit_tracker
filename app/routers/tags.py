"""
Tags endpoints: CRUD; deleting a tag also deletes the badges that use it.
"""

# Imports
import datetime as dt
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import owned_habit, owned_tag, user_today
from app.models import Habit, Tag
from app.schemas import BadgeRef, TagCreate, TagOut, TagUpdate
from app.services.tags import badges_using, delete_tag

router = APIRouter()


@router.get("/habits/{habit_id}/tags", status_code=200, response_model=list[TagOut])
def list_tags(habit: Habit = Depends(owned_habit), db: Session = Depends(get_db)):
    """Every tag of a habit, oldest first."""
    return db.scalars(select(Tag).where(Tag.habit_id == habit.id).order_by(Tag.created_at)).all()


@router.get("/tags/{tag_id}", status_code=200, response_model=TagOut)
def get_tag(tag: Tag = Depends(owned_tag)):
    """One tag."""
    return tag


@router.get("/tags/{tag_id}/badges", status_code=200, response_model=list[BadgeRef])
def list_tag_badges(tag: Tag = Depends(owned_tag), db: Session = Depends(get_db)):
    """Badges that use a tag: the ones deleting it would delete, for the warning."""
    return badges_using(db, tag)


@router.post("/habits/{habit_id}/tags", status_code=201, response_model=TagOut)
def create_tag(data: TagCreate, habit: Habit = Depends(owned_habit), db: Session = Depends(get_db)):
    """Creates a tag."""
    tag = Tag(habit_id=habit.id, name=data.name)
    db.add(tag)
    db.commit()
    return tag


@router.patch("/tags/{tag_id}", status_code=200, response_model=TagOut)
def update_tag(data: TagUpdate, tag: Tag = Depends(owned_tag), db: Session = Depends(get_db)):
    """Renames a tag."""

    # Update
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(tag, field, value)

    db.commit()
    return tag


@router.delete("/tags/{tag_id}", status_code=204)
def remove_tag(tag: Tag = Depends(owned_tag), today: dt.date = Depends(user_today), db: Session = Depends(get_db)):
    """Deletes a tag: gone from every session, and the badges that use it deleted too."""
    delete_tag(db, tag, today)
    db.commit()
