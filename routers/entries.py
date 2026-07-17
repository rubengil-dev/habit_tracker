from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Entries, Habits
from schemas import EntryCreate, EntryUpdate

router = APIRouter()

# GET ALL ENTRIES
@router.get("/entries", status_code=200)
def list_entries(db: Session = Depends(get_db)):
    return db.query(Entries).all()

# GET ALL ENTRIES FROM ONE HABIT
@router.get("/habits/{habit_id}/entries", status_code=200)
def list_entries_related(habit_id: int, db: Session = Depends(get_db)):
    habit = db.query(Habits).filter(Habits.id == habit_id).first()
    if habit is None:
        raise HTTPException(status_code=404, detail=f"Habit #{habit_id} not found")

    return db.query(Entries).filter(Entries.habit_id == habit_id).all()

# GET ONE ENTRY
@router.get("/entries/{id}", status_code=200)
def get_entry(id: int, db: Session = Depends(get_db)):
    entry = db.query(Entries).filter(Entries.id == id).first()

    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

# CREATE ENTRY
@router.post("/entries", status_code=201)
def create_entry(data: EntryCreate, db: Session = Depends(get_db)):
    new_entry = Entries(
        habit_id=data.habit_id,
        metric_id=data.metric_id,
        value=data.value,
        date=data.date
    )

    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry

# UPDATE ENTRY
@router.patch("/entries/{id}", status_code=200)
def update_entry(id: int, data: EntryUpdate, db: Session = Depends(get_db)):
    entry = db.query(Entries).filter(Entries.id == id).first()

    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(entry, key, value)

    db.commit()
    db.refresh(entry)
    return entry

# DELETE ENTRY
@router.delete("/entries/{id}", status_code=204)
def delete_entry(id: int, db: Session = Depends(get_db)):
    entry = db.query(Entries).filter(Entries.id == id).first()

    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")

    db.delete(entry)
    db.commit()