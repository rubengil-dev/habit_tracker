""""
This file creates de database schema.

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
from sqlalchemy import Column, Integer, Float, String, Boolean, Date, ForeignKey
from database import Base
from sqlalchemy import CheckConstraint
from enums import MetricType, Tier, FrequencyPeriod

# ENUMs use to protect BBDD's writting from any entry
_valid_metric_types = ", ".join(f"'{t.value}'" for t in MetricType)
_valid_tiers = ", ".join(f"'{t.value}'" for t in Tier)
_valid_frequency_periods = ", ".join(f"'{p.value}'" for p in FrequencyPeriod)

# HABITS
class Habits(Base):
    __tablename__ = "habits"

    # Columns
    id = Column(Integer, primary_key=True)
    habit = Column(String, nullable=False, unique=True)
    active = Column(Boolean, default=True)

    # Print managing
    def __repr__(self):

        if self.active:
            return f"Habit #{self.id} {self.habit} is active"
        else:
            return f"Habit #{self.id} {self.habit} is inactive"


# METRICS
class Metrics(Base):
    __tablename__ = "metrics"

    # Columns
    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False, index=True)
    metric = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    calculated = Column(Boolean, default=False)     # For secondary metrics as Pace (x/t) for Run
    formula = Column(String, nullable=True)         # How to calculate the secondary metric

    # Print managing
    def __repr__(self):
        return f"Metric #{self.id} {self.metric} belongs to habit #{self.habit_id}"
    
    # Constraints
    __table_args__ = (

        # If a metric is calculated = TRUE, formula cant be 0.
        CheckConstraint(
            "calculated = 0 OR (formula IS NOT NULL)",
            name="calculated_requires_formula"
        ),
    )

# BADGES
class Badges(Base):
    __tablename__ = "badges"

    # Columns
    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_id = Column(Integer, ForeignKey("metrics.id", ondelete="CASCADE"), nullable=False, index=True)
    badge = Column(String, nullable=False)
    metric_type = Column(String, nullable=False)            # Detailed in "enums.py"

    frequency_target = Column(Integer, nullable=True)       # How many times to do smth in "frequency_period"
    frequency_period = Column(String, nullable=True)        # See enums.py to check options of time window
    higher_is_better = Column(Boolean, default=True)        # Metrics as Pace is better as lower it is. Uncheck it in those cases
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

        # Tiers must follow one of the following rules:
        CheckConstraint(

            # Consistency and Objective are always Higher Is Better, tho tiers are always ASC
            "(metric_type IN ('consistency', 'objective') AND 0 < unlocked AND unlocked < bronze AND bronze < silver AND silver < gold AND gold < diamond) "
            "OR "

            # Historic and Top can be Higher is Better, tho tiers are ASC
            "(metric_type NOT IN ('consistency', 'objective') AND higher_is_better = 1 AND 0 < unlocked AND unlocked < bronze AND bronze < silver AND silver < gold AND gold < diamond) "
            "OR "

            # Or they can be Higher is NOT Better, tho tiers are DESC
            "(metric_type NOT IN ('consistency', 'objective') AND higher_is_better = 0 AND unlocked > bronze AND bronze > silver AND silver > gold AND gold > diamond AND diamond > 0)",
            name="tiers_check"
        ),

        # If metric_type is OBJECTIVE, threshold_value cant be NULL
        CheckConstraint(
            "(metric_type != 'objective') OR (threshold_value IS NOT NULL)",
            name="objective_requires_threshold"
        ),
        
        # If metric_type is CONSISTENCY, frequency target and period cant be NULL   
        CheckConstraint(
            "metric_type != 'consistency' OR (frequency_target IS NOT NULL AND frequency_period IS NOT NULL)",
            name="consistency_requires_frequency"
        ),

        # ENUM protection for METRIC_TYPE
        CheckConstraint(
            f"metric_type IN ({_valid_metric_types})",
            name="valid_metric_type"
        ),

        # ENUM protection for CURRENT_TIER
        CheckConstraint(
            f"current_tier IN ({_valid_tiers})",
            name="valid_current_tier"
        ),

        # ENUM protection for FREQUENCY_PERIOD
        CheckConstraint(
            f"frequency_period IS NULL OR frequency_period IN ({_valid_frequency_periods})",
            name="valid_frequency_period"
        )
    )

    # Print managing
    def __repr__(self):
        return f"Badge #{self.id} {self.badge} belongs to habit #{self.habit_id} and current tier is {self.current_tier}"

# DATA ENTRY
class Entries(Base):
    __tablename__ = "entries"

    # Columns
    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_id = Column(Integer, ForeignKey("metrics.id", ondelete="CASCADE"), nullable=False, index=True)
    value = Column(Float, nullable=False)
    date = Column(Date, nullable=False)

    # Print managing
    def __repr__(self):
        return f"Entry #{self.id} on day {self.date} refers to habit #{self.habit_id} and metric #{self.metric_id} with value {self.value}."
