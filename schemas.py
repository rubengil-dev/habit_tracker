"""
This script creates every Pydantic model needed
"""

from pydantic import BaseModel
from typing import Optional
from datetime import date as d_date

## HABIT SCHEMAS

# CREATION
class HabitCreate(BaseModel):
    habit: str
    active: bool = True

# UPDATE
class HabitUpdate(BaseModel):
    habit: Optional[str] = None
    active: Optional[bool] = None

## METRIC SCHEMAS

# CREATION
class MetricCreate(BaseModel):
    metric: str
    unit: str
    habit_id: int
    calculated: bool = False
    formula: Optional[str] = None

# UPDATE
class MetricUpdate(BaseModel):
    metric: Optional[str] = None
    unit: Optional[str] = None
    habit_id: Optional[int] = None
    calculated: Optional[bool] = None
    formula: Optional[str] = None

## BADGE SCHEMAS

# CREATION
class BadgeCreate(BaseModel):
    habit_id: int
    metric_id: int
    badge: str
    metric_type: str
    unlocked: int
    bronze: int
    silver: int
    gold: int
    diamond: int
    current_value: Optional[int] = 0
    current_tier: Optional[str] = 'unlocked'


# UPDATE
class BadgeUpdate(BaseModel):
    habit_id: Optional[int] = None
    metric_id: Optional[int] = None
    badge: Optional[str] = None
    metric_type: Optional[str] = None
    unlocked: Optional[int] = None
    bronze: Optional[int] = None
    silver: Optional[int] = None
    gold: Optional[int] = None
    diamond: Optional[int] = None
    current_value: Optional[int] = None
    current_tier: Optional[str] = None

## ENTRY SCHEMAS

# CREATION
class EntryCreate(BaseModel):
    habit_id: int
    metric_id: int
    value: float
    date: d_date

# UPDATE
class EntryUpdate(BaseModel):
    habit_id: Optional[int] = None
    metric_id: Optional[int] = None
    value: Optional[float] = None
    date: Optional[d_date] = None