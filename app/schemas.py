"""
API schemas (Pydantic):
    - Input: create and update bodies; values the server sets never come in, unknown fields are rejected
    - Output: what the API returns, built from table rows
    - Update bodies: every field can be left out, but sent as null only where the field allows it
"""

# Imports
import datetime as dt
from typing import Annotated
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from app.enums import GoalMode, MetricKind, Period

# Text fields
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
Unit = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]


class Input(BaseModel):
    """Base of every request body: unknown fields are rejected."""

    model_config = ConfigDict(extra="forbid")


class Output(BaseModel):
    """Base of every response: read from table rows."""

    model_config = ConfigDict(from_attributes=True)


# Auth

class LoginIn(Input):
    username: str
    password: str


class UserOut(Output):
    username: str
    timezone: str


class UserUpdate(Input):
    timezone: str = None

    @field_validator("timezone")
    @classmethod
    def known_timezone(cls, value: str) -> str:
        """IANA name, such as Europe/Madrid."""
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError(f"Unknown timezone: {value}")
        return value


# Habits

class HabitCreate(Input):
    name: Name
    active: bool = True
    start_date: dt.date | None = None           # Today if left out
    goal_target: int = Field(ge=0)
    goal_period: Period
    goal_mode: GoalMode = GoalMode.MIN

    @model_validator(mode="after")
    def reachable_goal(self):
        """"At least 0" is always met: only "at most 0" (avoid) can have a 0."""
        if self.goal_target == 0 and self.goal_mode == GoalMode.MIN:
            raise ValueError("A goal of at least 0 is always met: use at least 1, or at most 0")
        return self


class HabitUpdate(Input):
    name: Name = None
    active: bool = None
    start_date: dt.date = None
    goal_target: int = Field(default=None, ge=0)
    goal_period: Period = None
    goal_mode: GoalMode = None


class HabitOut(Output):
    id: UUID
    name: str
    active: bool
    start_date: dt.date
    goal_target: int
    goal_period: Period
    goal_mode: GoalMode
    created_at: dt.datetime


class HabitDetailOut(HabitOut):
    current_streak: int
    best_streak: int


# Metrics

class MetricCreate(Input):
    name: Name
    unit: Unit | None = None
    kind: MetricKind
    operand_a_id: UUID | None = None            # Ratio: A ÷ B
    operand_b_id: UUID | None = None

    @model_validator(mode="after")
    def ratio_operands(self):
        """A ratio needs two different operands; typed-in metrics have none."""
        operands = (self.operand_a_id, self.operand_b_id)

        if self.kind == MetricKind.RATIO and None in operands:
            raise ValueError("A ratio needs operand_a_id and operand_b_id")
        if self.kind == MetricKind.RATIO and self.operand_a_id == self.operand_b_id:
            raise ValueError("A ratio needs two different operands")
        if self.kind != MetricKind.RATIO and operands != (None, None):
            raise ValueError("Only ratio metrics have operands")
        return self


class MetricUpdate(Input):
    name: Name = None
    unit: Unit | None = None                    # null clears it


class MetricOut(Output):
    id: UUID
    habit_id: UUID
    name: str
    unit: str | None
    kind: MetricKind
    operand_a_id: UUID | None
    operand_b_id: UUID | None
    created_at: dt.datetime


# Tags

class TagCreate(Input):
    name: Name


class TagUpdate(Input):
    name: Name = None


class TagOut(Output):
    id: UUID
    habit_id: UUID
    name: str
    created_at: dt.datetime


class BadgeRef(Output):
    id: UUID
    name: str
