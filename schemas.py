"""
Pydantic schemas:
    - Create, update and response per entity
    - Write response for entries
"""

# Imports
from pydantic import BaseModel
from typing import Optional
from datetime import date as d_date

from enums import MetricType, Tier, FrequencyPeriod

# Habits

# Create
class HabitCreate(BaseModel):
    habit: str
    active: bool = True

# Update
class HabitUpdate(BaseModel):
    habit: Optional[str] = None
    active: Optional[bool] = None

# Response
class HabitResponse(BaseModel):
    id: int
    habit: str
    active: bool

    class Config:
        from_attributes = True

# Metrics

# Create
class MetricCreate(BaseModel):
    metric: str
    unit: str
    habit_id: int
    calculated: bool = False
    formula: Optional[str] = None

# Update
class MetricUpdate(BaseModel):
    metric: Optional[str] = None
    unit: Optional[str] = None
    habit_id: Optional[int] = None
    calculated: Optional[bool] = None
    formula: Optional[str] = None

# Response
class MetricResponse(BaseModel):
    id: int
    habit_id: int
    metric: str
    unit: str
    calculated: bool
    formula: Optional[str] = None

    class Config:
        from_attributes = True

# Badges

# Create
class BadgeCreate(BaseModel):
    habit_id: int
    metric_id: int
    badge: str
    metric_type: MetricType
    unlocked: float
    bronze: float
    silver: float
    gold: float
    diamond: float
    frequency_target: Optional[int] = None
    frequency_period: Optional[FrequencyPeriod] = None
    higher_is_better: bool = True
    threshold_value: Optional[float] = None


# Update
class BadgeUpdate(BaseModel):
    habit_id: Optional[int] = None
    metric_id: Optional[int] = None
    badge: Optional[str] = None
    metric_type: Optional[MetricType] = None
    unlocked: Optional[float] = None
    bronze: Optional[float] = None
    silver: Optional[float] = None
    gold: Optional[float] = None
    diamond: Optional[float] = None
    frequency_target: Optional[int] = None
    frequency_period: Optional[FrequencyPeriod] = None
    higher_is_better: Optional[bool] = None
    threshold_value: Optional[float] = None

# Response
class BadgeResponse(BaseModel):
    id: int
    habit_id: int
    metric_id: int
    badge: str
    metric_type: MetricType
    unlocked: float
    bronze: float
    silver: float
    gold: float
    diamond: float
    current_value: Optional[float] = None
    current_tier: Optional[Tier] = None
    frequency_target: Optional[int] = None
    frequency_period: Optional[FrequencyPeriod] = None
    higher_is_better: bool
    threshold_value: Optional[float] = None
    current_progress: Optional[tuple[int, int]] = None

    class Config:
        from_attributes = True

# Entries

# Create
class EntryCreate(BaseModel):
    habit_id: int
    metric_id: int
    value: float
    date: d_date

# Update
class EntryUpdate(BaseModel):
    habit_id: Optional[int] = None
    metric_id: Optional[int] = None
    value: Optional[float] = None
    date: Optional[d_date] = None

# Response
class EntryResponse(BaseModel):
    id: int
    habit_id: int
    metric_id: int
    value: float
    date: d_date

    class Config:
        from_attributes = True

# Write response: entry + side effects of create, update and delete
class EntryWriteResponse(BaseModel):
    entry: Optional[EntryResponse] = None
    badges_update: list[BadgeResponse]
    streak_update: int
