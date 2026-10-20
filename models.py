"""
Database tables:

 HABITS
    |
    | habit_id
    ├──────────────> BADGES
    |                   ^
    |                   | metric_id
    | habit_id          |
    ├──────────────> METRICS
    |                   |
    |                   | metric_id
    | habit_id          v
    └──────────────> ENTRIES
"""

# Imports
from sqlalchemy import Column, Integer, Float, String, Boolean, Date, ForeignKey, CheckConstraint

from database import Base
from enums import MetricType, Tier, FrequencyPeriod

# Enum values for CHECK constraints
_valid_metric_types = ", ".join(f"'{t.value}'" for t in MetricType)
_valid_tiers = ", ".join(f"'{t.value}'" for t in Tier)
_valid_frequency_periods = ", ".join(f"'{p.value}'" for p in FrequencyPeriod)

# Habits
class Habits(Base):
    __tablename__ = "habits"

    # Columns
    id = Column(Integer, primary_key=True)
    habit = Column(String, nullable=False, unique=True)
    active = Column(Boolean, default=True)

    # Representation
    def __repr__(self):

        if self.active:
            return f"Habit #{self.id} {self.habit} is active"
        else:
            return f"Habit #{self.id} {self.habit} is inactive"


# Metrics
class Metrics(Base):
    __tablename__ = "metrics"

    # Columns
    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False, index=True)
    metric = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    calculated = Column(Boolean, default=False)     # Secondary metrics, as Pace (x/t) for Run
    formula = Column(String, nullable=True)         # How to calculate the secondary metric

    # Representation
    def __repr__(self):
        return f"Metric #{self.id} {self.metric} belongs to habit #{self.habit_id}"

    # Constraints
    __table_args__ = (

        # A calculated metric needs a formula
        CheckConstraint(
            "calculated = 0 OR (formula IS NOT NULL)",
            name="calculated_requires_formula"
        ),
    )

# Badges
class Badges(Base):
    __tablename__ = "badges"

    # Columns
    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_id = Column(Integer, ForeignKey("metrics.id", ondelete="CASCADE"), nullable=False, index=True)
    badge = Column(String, nullable=False)
    metric_type = Column(String, nullable=False)            # See enums.py

    frequency_target = Column(Integer, nullable=True)       # How many times to do something in "frequency_period"
    frequency_period = Column(String, nullable=True)        # See enums.py
    higher_is_better = Column(Boolean, default=True)        # False for metrics as Pace, where lower is better
    threshold_value = Column(Float, nullable=True)          # Needed for metric_type "objective"

    unlocked = Column(Float, nullable=False)
    bronze = Column(Float, nullable=False)
    silver = Column(Float, nullable=False)
    gold = Column(Float, nullable=False)
    diamond = Column(Float, nullable=False)

    current_value = Column(Float, default=0)
    current_tier = Column(String, default="locked")

    # Constraints
    __table_args__ = (

        # Tiers order
        CheckConstraint(

            # Consistency and Objective: counts, so tiers are always ASC
            "(metric_type IN ('consistency', 'objective') AND 0 < unlocked AND unlocked < bronze AND bronze < silver AND silver < gold AND gold < diamond) "
            "OR "

            # Historic and Top, higher is better: tiers ASC
            "(metric_type NOT IN ('consistency', 'objective') AND higher_is_better = 1 AND 0 < unlocked AND unlocked < bronze AND bronze < silver AND silver < gold AND gold < diamond) "
            "OR "

            # Historic and Top, lower is better: tiers DESC
            "(metric_type NOT IN ('consistency', 'objective') AND higher_is_better = 0 AND unlocked > bronze AND bronze > silver AND silver > gold AND gold > diamond AND diamond > 0)",
            name="tiers_check"
        ),

        # Objective needs a threshold
        CheckConstraint(
            "(metric_type != 'objective') OR (threshold_value IS NOT NULL)",
            name="objective_requires_threshold"
        ),

        # Consistency needs frequency target and period
        CheckConstraint(
            "metric_type != 'consistency' OR (frequency_target IS NOT NULL AND frequency_period IS NOT NULL)",
            name="consistency_requires_frequency"
        ),

        # Enum protection: metric_type
        CheckConstraint(
            f"metric_type IN ({_valid_metric_types})",
            name="valid_metric_type"
        ),

        # Enum protection: current_tier
        CheckConstraint(
            f"current_tier IN ({_valid_tiers})",
            name="valid_current_tier"
        ),

        # Enum protection: frequency_period
        CheckConstraint(
            f"frequency_period IS NULL OR frequency_period IN ({_valid_frequency_periods})",
            name="valid_frequency_period"
        )
    )

    # Representation
    def __repr__(self):
        return f"Badge #{self.id} {self.badge} belongs to habit #{self.habit_id} and current tier is {self.current_tier}"

# Entries
class Entries(Base):
    __tablename__ = "entries"

    # Columns
    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_id = Column(Integer, ForeignKey("metrics.id", ondelete="CASCADE"), nullable=False, index=True)
    value = Column(Float, nullable=False)
    date = Column(Date, nullable=False)

    # Representation
    def __repr__(self):
        return f"Entry #{self.id} on day {self.date} refers to habit #{self.habit_id} and metric #{self.metric_id} with value {self.value}."
