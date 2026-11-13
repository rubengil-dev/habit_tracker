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
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError, field_validator, model_validator

from app.enums import BadgeKind, GoalMode, MetricKind, Period, TagRule, Tier
from app.services.badge_rules import check_badge

# Text fields
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
Unit = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]

# Number fields: never negative, no infinity or NaN
Value = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Threshold = Annotated[float, Field(gt=0, allow_inf_nan=False)]


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
            raise ValueError(f"Unknown timezone: {value}") from None
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


# Entries: sessions

class EntryCreate(Input):
    date: dt.date | None = None                 # Today if left out
    values: dict[UUID, Value] = {}              # Typed-in metric id → value; durations in seconds
    tag_ids: list[UUID] = []


class EntryUpdate(Input):
    date: dt.date = None
    values: dict[UUID, Value] = None            # Replaces every typed-in value
    tag_ids: list[UUID] = None                  # Replaces every tag


class EntryOut(Output):
    id: UUID
    habit_id: UUID
    date: dt.date
    values: dict[UUID, float]                   # Ratios included
    tag_ids: list[UUID] = Field(validation_alias="tags")
    created_at: dt.datetime

    @field_validator("values", mode="before")
    @classmethod
    def values_by_metric(cls, rows):
        """Value rows → {metric id: value}."""
        return {row.metric_id: row.value for row in rows} if isinstance(rows, list) else rows

    @field_validator("tag_ids", mode="before")
    @classmethod
    def ids_of_tags(cls, tags):
        """Tag rows → their ids."""
        return [tag.id for tag in tags]


class BadgeChangeOut(BaseModel):
    badge_id: UUID
    name: str
    old_value: float | None
    new_value: float | None
    old_tier: Tier
    new_tier: Tier

    @classmethod
    def from_change(cls, change) -> "BadgeChangeOut":
        """Badge change of the recalculation → its response."""
        badge = change.badge
        return cls(
            badge_id=badge.id, name=badge.name,
            old_value=change.old_value, new_value=badge.current_value,
            old_tier=change.old_tier, new_tier=badge.current_tier,
        )


class EffectsOut(BaseModel):
    badge_changes: list[BadgeChangeOut]
    current_streak: int
    best_streak: int


class EntryWriteOut(EffectsOut):
    entry: EntryOut


# Badges

class BadgeCreate(Input):
    name: Name
    kind: BadgeKind
    metric_id: UUID | None = None
    higher_is_better: bool = True
    threshold: Value | None = None
    period: Period | None = None
    target: int | None = Field(default=None, ge=0)
    mode: GoalMode | None = None
    untagged_only: bool = False
    required_tag_ids: list[UUID] = []
    excluded_tag_ids: list[UUID] = []
    unlocked: Threshold
    bronze: Threshold
    silver: Threshold
    gold: Threshold
    diamond: Threshold

    @model_validator(mode="after")
    def coherent(self):
        """Fields each kind needs and none it does not use, tag filters that fit together, tiers in order."""
        check_badge(self)
        return self


class BadgeUpdate(Input):
    name: Name = None
    higher_is_better: bool = None
    threshold: Value | None = None
    period: Period | None = None
    target: int | None = Field(default=None, ge=0)
    mode: GoalMode | None = None
    untagged_only: bool = None
    required_tag_ids: list[UUID] = None
    excluded_tag_ids: list[UUID] = None
    unlocked: Threshold = None
    bronze: Threshold = None
    silver: Threshold = None
    gold: Threshold = None
    diamond: Threshold = None


class ProgressOut(BaseModel):
    period_count: int
    target: int
    current_streak: int | None


class BadgeOut(Output):
    id: UUID
    habit_id: UUID
    metric_id: UUID | None
    name: str
    kind: BadgeKind
    higher_is_better: bool
    threshold: float | None
    period: Period | None
    target: int | None
    mode: GoalMode | None
    untagged_only: bool
    required_tag_ids: list[UUID] = Field(validation_alias="tag_rules")
    excluded_tag_ids: list[UUID] = Field(validation_alias="tag_rules")
    unlocked: float
    bronze: float
    silver: float
    gold: float
    diamond: float
    current_value: float | None
    current_tier: Tier
    created_at: dt.datetime
    progress: ProgressOut | None = None         # Consistency and streak badges

    @field_validator("required_tag_ids", mode="before")
    @classmethod
    def required_tags(cls, rules):
        """Tag rules → ids of the required tags."""
        return [rule.tag_id for rule in rules if rule.rule == TagRule.REQUIRED]

    @field_validator("excluded_tag_ids", mode="before")
    @classmethod
    def excluded_tags(cls, rules):
        """Tag rules → ids of the excluded tags."""
        return [rule.tag_id for rule in rules if rule.rule == TagRule.EXCLUDED]


class TiersOut(BaseModel):
    tiers: list[float]


# Today

class TodayHabitOut(BaseModel):
    habit: HabitOut
    today_count: int                            # Sessions today
    period_count: int                           # Sessions in the goal's current period
    goal_met: bool                              # At least n: reached. At most n: not gone over, so far
    current_streak: int
    best_streak: int


class TodayOut(BaseModel):
    date: dt.date
    habits: list[TodayHabitOut]
    badge_changes: list[BadgeChangeOut]         # Avoid badges that went up since the last visit


# Export

class HabitExportOut(HabitOut):
    metrics: list[MetricOut]
    tags: list[TagOut]
    entries: list[EntryOut]
    badges: list[BadgeOut]


class ExportOut(BaseModel):
    format_version: int = 1
    exported_at: dt.datetime
    user: UserOut
    habits: list[HabitExportOut]


# Updates checked as a whole

def check_as_whole(schema: type[BaseModel], row, changes: dict, extra: dict | None = None) -> BaseModel:
    """
    A row as it would end up after a partial update, checked with the rules of a new one → 422 if it breaks one:
        - extra: current values the row does not hold as columns (a badge's tag ids)
    """
    current = {field: getattr(row, field) for field in schema.model_fields if hasattr(row, field)}

    try:
        return schema.model_validate(current | (extra or {}) | changes)
    except ValidationError as error:
        raise RequestValidationError(error.errors()) from error

