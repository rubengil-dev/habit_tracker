from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Metrics, Habits
from schemas import MetricCreate, MetricUpdate

router = APIRouter()

# GET ALL METRICS
@router.get("/metrics", status_code=200)
def list_metrics(db: Session = Depends(get_db)):
    """Returns every single metric created."""

    # Query itself
    return db.query(Metrics).all()

# GET ALL METRICS FROM ONE HABIT
@router.get("/habits/{habit_id}/metrics", status_code=200)
def list_metrics_related(habit_id: int, db: Session = Depends(get_db)):
    """Returns every single metric created for a concrete habit."""

    # Habit existence check
    habit = db.query(Habits).filter(Habits.id == habit_id).first()

    if habit is None:
        raise HTTPException(status_code=404, detail=f"Habit #{habit_id} not found")
    
    # Query itself
    return db.query(Metrics).filter(Metrics.habit_id == habit_id).all()

# GET ONE METRIC
@router.get("/metrics/{id}", status_code=200)
def get_metric(id: int, db: Session = Depends(get_db)):
    """Returns only one metric."""

    # Query itself
    metric = db.query(Metrics).filter(Metrics.id == id).first()

    # Error managing if metric doesnt exists
    if metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")
    return metric

# CREATE METRIC
@router.post("/metrics", status_code=201)
def create_metric(data: MetricCreate, db: Session = Depends(get_db)):
    """Creates a new metric."""

    # Habit existence check
    habit = db.query(Habits).filter(Habits.id == data.habit_id).first()

    if habit is None:
        raise HTTPException(status_code=404, detail=f"Habit #{data.habit_id} not found")
    
    # Metric creation
    new_metric = Metrics(
        habit_id=data.habit_id,
        metric=data.metric,
        unit=data.unit,
        calculated=data.calculated,
        formula=data.formula
    )   

    # DataBase updates
    db.add(new_metric)
    db.commit()
    db.refresh(new_metric)
    return new_metric

# UPDATE METRICS
@router.patch("/metrics/{id}", status_code=200)
def update_metric(id: int, data: MetricUpdate, db: Session = Depends(get_db)):
    """Updates an existing metric using a loop (model_dump)."""

    # Query itself
    metric = db.query(Metrics).filter(Metrics.id == id).first()

    # Error managing if metric doesnt exists
    if metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")
    
    # Update itself
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(metric, key, value)

    # DataBase update
    db.commit()
    db.refresh(metric)
    return metric

# DELETE METRIC
@router.delete("/metrics/{id}", status_code=204)
def delete_metric(id: int, db: Session = Depends(get_db)):
    """Deletes an existing metric."""

    # Query itself
    metric = db.query(Metrics).filter(Metrics.id == id).first()

    # Error managing if metric doesnt exists
    if metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")
    
    # DataBase update
    db.delete(metric)
    db.commit()