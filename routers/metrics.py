"""
Metrics endpoints: CRUD.
"""

# Imports
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Metrics, Habits
from schemas import MetricCreate, MetricUpdate, MetricResponse

router = APIRouter()


@router.get("/metrics", status_code=200, response_model=list[MetricResponse])
def list_metrics(db: Session = Depends(get_db)):
    """Returns every metric."""

    # Query
    return db.query(Metrics).all()


@router.get("/habits/{habit_id}/metrics", status_code=200, response_model=list[MetricResponse])
def list_metrics_related(habit_id: int, db: Session = Depends(get_db)):
    """Returns every metric of a habit."""

    # Habit check
    habit = db.query(Habits).filter(Habits.id == habit_id).first()

    if habit is None:
        raise HTTPException(status_code=404, detail=f"Habit #{habit_id} not found")

    # Query
    return db.query(Metrics).filter(Metrics.habit_id == habit_id).all()


@router.get("/metrics/{id}", status_code=200, response_model=MetricResponse)
def get_metric(id: int, db: Session = Depends(get_db)):
    """Returns one metric."""

    # Query
    metric = db.query(Metrics).filter(Metrics.id == id).first()

    # Existence check
    if metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")
    return metric


@router.post("/metrics", status_code=201, response_model=MetricResponse)
def create_metric(data: MetricCreate, db: Session = Depends(get_db)):
    """Creates a metric."""

    # Habit check
    habit = db.query(Habits).filter(Habits.id == data.habit_id).first()

    if habit is None:
        raise HTTPException(status_code=404, detail=f"Habit #{data.habit_id} not found")

    # Create
    new_metric = Metrics(
        habit_id=data.habit_id,
        metric=data.metric,
        unit=data.unit,
        calculated=data.calculated,
        formula=data.formula
    )

    # Save
    db.add(new_metric)
    db.commit()
    db.refresh(new_metric)
    return new_metric


@router.patch("/metrics/{id}", status_code=200, response_model=MetricResponse)
def update_metric(id: int, data: MetricUpdate, db: Session = Depends(get_db)):
    """Updates a metric."""

    # Query
    metric = db.query(Metrics).filter(Metrics.id == id).first()

    # Existence check
    if metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")

    # Update
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(metric, key, value)

    # Save
    db.commit()
    db.refresh(metric)
    return metric


@router.delete("/metrics/{id}", status_code=204)
def delete_metric(id: int, db: Session = Depends(get_db)):
    """Deletes a metric and its entries and badges."""

    # Query
    metric = db.query(Metrics).filter(Metrics.id == id).first()

    # Existence check
    if metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")

    # Save
    db.delete(metric)
    db.commit()
