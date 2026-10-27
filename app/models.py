"""
Database tables:

 USERS
    ├──> AUTH_SESSIONS
    └──> HABITS
            ├──> METRICS ──(operands A, B)──> METRICS        Ratio metrics
            ├──> TAGS
            ├──> ENTRIES                                     Sessions of a habit
            |       ├──> ENTRY_VALUES  <── METRICS           One per metric filled in
            |       └──> ENTRY_TAGS    <── TAGS
            └──> BADGES  <── METRICS (optional)
                    └──> BADGE_TAGS    <── TAGS              Required or excluded

Every foreign key deletes in cascade.
"""

# Imports
import datetime as dt
from uuid import UUID, uuid4
from sqlalchemy import CheckConstraint, Column, DateTime, Enum, ForeignKey, Table, TypeDecorator, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import BadgeKind, GoalMode, MetricKind, Period, TagRule, Tier

# Tiers order: descending only in historic and record when lower is better
DESCENDING = "kind IN ('historic', 'record') AND higher_is_better = false"
ASCENDING_TIERS = "0 < unlocked AND unlocked < bronze AND bronze < silver AND silver < gold AND gold < diamond"
DESCENDING_TIERS = "unlocked > bronze AND bronze > silver AND silver > gold AND gold > diamond AND diamond > 0"


# Column types

def enum_type(enum_class: type, name: str) -> Enum:
    """Plain text column, restricted to the enum values by a CHECK constraint generated from the enum."""
    return Enum(
        enum_class, name=name, native_enum=False, create_constraint=True, length=20,
        values_callable=lambda members: [member.value for member in members],
    )


class UTCDateTime(TypeDecorator):
    """Timezone-aware datetime. SQLite (tests) returns it naive, so UTC is added back."""

    impl = DateTime
    cache_ok = True

    def __init__(self):
        """Always with timezone."""
        super().__init__(timezone=True)

    def process_result_value(self, value, dialect):
        """Naive datetime → UTC datetime."""
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=dt.UTC)
        return value


def now_utc() -> dt.datetime:
    """Current UTC time, for created_at columns."""
    return dt.datetime.now(dt.UTC)


class Entity:
    """Columns of every main table: UUID id first, creation time last."""

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4, sort_order=-1)
    created_at: Mapped[dt.datetime] = mapped_column(UTCDateTime(), default=now_utc, sort_order=1)


# Users

class User(Entity, Base):
    __tablename__ = "users"

    # Columns
    username: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    timezone: Mapped[str] = mapped_column(default="Europe/Madrid")
    failed_logins: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[dt.datetime | None] = mapped_column(UTCDateTime())


class AuthSession(Entity, Base):
    __tablename__ = "auth_sessions"

    # Columns
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(unique=True)        # SHA-256 of the cookie token
    expires_at: Mapped[dt.datetime] = mapped_column(UTCDateTime())

    # Parent
    user: Mapped["User"] = relationship(lazy="joined")


# Habits

class Habit(Entity, Base):
    __tablename__ = "habits"

    # Columns
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str]
    active: Mapped[bool] = mapped_column(default=True)
    start_date: Mapped[dt.date]
    goal_target: Mapped[int]
    goal_period: Mapped[Period] = mapped_column(enum_type(Period, "period"))
    goal_mode: Mapped[GoalMode] = mapped_column(enum_type(GoalMode, "goal_mode"), default=GoalMode.MIN)

    # Children
    metrics: Mapped[list["Metric"]] = relationship(order_by="Metric.created_at", cascade="all, delete-orphan", passive_deletes=True)
    tags: Mapped[list["Tag"]] = relationship(order_by="Tag.created_at", cascade="all, delete-orphan", passive_deletes=True)
    entries: Mapped[list["Entry"]] = relationship(order_by="Entry.date", cascade="all, delete-orphan", passive_deletes=True)
    badges: Mapped[list["Badge"]] = relationship(order_by="Badge.created_at", cascade="all, delete-orphan", passive_deletes=True)

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "name"),

        # "At least 0" is always met; "at most 0" is a valid avoid goal
        CheckConstraint("goal_target > 0 OR (goal_mode = 'max' AND goal_target = 0)", name="goal_target_valid"),
    )


# Metrics

class Metric(Entity, Base):
    __tablename__ = "metrics"

    # Columns
    habit_id: Mapped[UUID] = mapped_column(ForeignKey("habits.id", ondelete="CASCADE"), index=True)
    name: Mapped[str]
    unit: Mapped[str | None]
    kind: Mapped[MetricKind] = mapped_column(enum_type(MetricKind, "metric_kind"))
    operand_a_id: Mapped[UUID | None] = mapped_column(ForeignKey("metrics.id", ondelete="CASCADE"), index=True)
    operand_b_id: Mapped[UUID | None] = mapped_column(ForeignKey("metrics.id", ondelete="CASCADE"), index=True)

    # Constraints
    __table_args__ = (
        UniqueConstraint("habit_id", "name"),

        # A ratio needs two different operands; typed-in metrics have none
        CheckConstraint(
            "(kind = 'ratio' AND operand_a_id IS NOT NULL AND operand_b_id IS NOT NULL AND operand_a_id <> operand_b_id) "
            "OR (kind <> 'ratio' AND operand_a_id IS NULL AND operand_b_id IS NULL)",
            name="ratio_operands",
        ),
    )


# Tags

class Tag(Entity, Base):
    __tablename__ = "tags"

    # Columns
    habit_id: Mapped[UUID] = mapped_column(ForeignKey("habits.id", ondelete="CASCADE"), index=True)
    name: Mapped[str]

    # Constraints
    __table_args__ = (UniqueConstraint("habit_id", "name"),)


# Entries: sessions of a habit

entry_tags = Table(
    "entry_tags",
    Base.metadata,
    Column("entry_id", ForeignKey("entries.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, index=True),
)


class Entry(Entity, Base):
    __tablename__ = "entries"

    # Columns
    habit_id: Mapped[UUID] = mapped_column(ForeignKey("habits.id", ondelete="CASCADE"), index=True)
    date: Mapped[dt.date]

    # Children
    values: Mapped[list["EntryValue"]] = relationship(cascade="all, delete-orphan", passive_deletes=True, lazy="selectin")
    tags: Mapped[list["Tag"]] = relationship(secondary=entry_tags, lazy="selectin")


class EntryValue(Base):
    __tablename__ = "entry_values"

    # Columns
    entry_id: Mapped[UUID] = mapped_column(ForeignKey("entries.id", ondelete="CASCADE"), primary_key=True)
    metric_id: Mapped[UUID] = mapped_column(ForeignKey("metrics.id", ondelete="CASCADE"), primary_key=True, index=True)
    value: Mapped[float]            # Durations in seconds; ratios in raw units (A ÷ B)


# Badges

class Badge(Entity, Base):
    __tablename__ = "badges"

    # Columns
    habit_id: Mapped[UUID] = mapped_column(ForeignKey("habits.id", ondelete="CASCADE"), index=True)
    metric_id: Mapped[UUID | None] = mapped_column(ForeignKey("metrics.id", ondelete="CASCADE"), index=True)
    name: Mapped[str]
    kind: Mapped[BadgeKind] = mapped_column(enum_type(BadgeKind, "badge_kind"))
    higher_is_better: Mapped[bool] = mapped_column(default=True)
    threshold: Mapped[float | None]             # Bar a session's metric value must pass
    period: Mapped[Period | None] = mapped_column(enum_type(Period, "period"))
    target: Mapped[int | None]                  # Sessions per period
    mode: Mapped[GoalMode | None] = mapped_column(enum_type(GoalMode, "goal_mode"))
    untagged_only: Mapped[bool] = mapped_column(default=False)

    # Tier thresholds
    unlocked: Mapped[float]
    bronze: Mapped[float]
    silver: Mapped[float]
    gold: Mapped[float]
    diamond: Mapped[float]

    # Set by the server only
    current_value: Mapped[float | None]         # None: nothing to measure yet
    current_tier: Mapped[Tier] = mapped_column(enum_type(Tier, "tier"), default=Tier.LOCKED)

    # Children
    tag_rules: Mapped[list["BadgeTag"]] = relationship(cascade="all, delete-orphan", passive_deletes=True, lazy="selectin")

    # Constraints
    __table_args__ = (
        CheckConstraint(f"(({DESCENDING}) AND {DESCENDING_TIERS}) OR (NOT ({DESCENDING}) AND {ASCENDING_TIERS})", name="tiers_order"),
        CheckConstraint("kind <> 'record' OR metric_id IS NOT NULL", name="record_needs_metric"),
        CheckConstraint("kind <> 'objective' OR threshold IS NOT NULL", name="objective_needs_threshold"),
        CheckConstraint("threshold IS NULL OR metric_id IS NOT NULL", name="threshold_needs_metric"),
        CheckConstraint(
            "kind NOT IN ('consistency', 'streak') OR (period IS NOT NULL AND target IS NOT NULL AND mode IS NOT NULL)",
            name="periodic_needs_goal",
        ),
        CheckConstraint("target IS NULL OR target > 0 OR (mode = 'max' AND target = 0)", name="target_valid"),
    )


class BadgeTag(Base):
    __tablename__ = "badge_tags"

    # Columns
    badge_id: Mapped[UUID] = mapped_column(ForeignKey("badges.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[UUID] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, index=True)
    rule: Mapped[TagRule] = mapped_column(enum_type(TagRule, "tag_rule"))

    # Parent
    tag: Mapped["Tag"] = relationship(lazy="joined")
