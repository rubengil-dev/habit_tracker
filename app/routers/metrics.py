"""
Metrics endpoints: CRUD; a new ratio is filled in for every past session.
"""

# Imports
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import find_in_habit, owned_habit, owned_metric
from app.enums import MetricKind
from app.models import Habit, Metric
from app.schemas import MetricCreate, MetricOut, MetricUpdate
from app.services.ratios import backfill_ratio

router = APIRouter()


@router.get("/habits/{habit_id}/metrics", status_code=200, response_model=list[MetricOut])
def list_metrics(habit: Habit = Depends(owned_habit), db: Session = Depends(get_db)):
    """Every metric of a habit, oldest first."""
    return db.scalars(select(Metric).where(Metric.habit_id == habit.id).order_by(Metric.created_at)).all()


@router.get("/metrics/{metric_id}", status_code=200, response_model=MetricOut)
def get_metric(metric: Metric = Depends(owned_metric)):
    """One metric."""
    return metric


@router.post("/habits/{habit_id}/metrics", status_code=201, response_model=MetricOut)
def create_metric(data: MetricCreate, habit: Habit = Depends(owned_habit), db: Session = Depends(get_db)):
    """Creates a metric; a ratio is calculated at once for every past session."""
    if data.kind == MetricKind.RATIO:
        check_operands(db, habit, data)

    # Create
    metric = Metric(
        habit_id=habit.id,
        name=data.name,
        unit=data.unit,
        kind=data.kind,
        operand_a_id=data.operand_a_id,
        operand_b_id=data.operand_b_id,
    )
    db.add(metric)

    if metric.kind == MetricKind.RATIO:
        backfill_ratio(db, metric)

    db.commit()
    return metric


@router.patch("/metrics/{metric_id}", status_code=200, response_model=MetricOut)
def update_metric(data: MetricUpdate, metric: Metric = Depends(owned_metric), db: Session = Depends(get_db)):
    """Renames a metric or changes its unit; its kind and operands are fixed."""

    # Update
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(metric, field, value)

    db.commit()
    return metric


@router.delete("/metrics/{metric_id}", status_code=204)
def delete_metric(metric: Metric = Depends(owned_metric), db: Session = Depends(get_db)):
    """Deletes a metric with its values, the ratios that use it and the badges of all of them."""
    db.delete(metric)
    db.commit()


def check_operands(db: Session, habit: Habit, data: MetricCreate):
    """A ratio's operands: metrics of the same habit (404 / 400), and not ratios themselves (400)."""
    for operand in find_in_habit(db, Metric, [data.operand_a_id, data.operand_b_id], habit):
        if operand.kind == MetricKind.RATIO:
            raise HTTPException(status_code=400, detail=f"{operand.name} is a ratio: a ratio cannot use another one")
