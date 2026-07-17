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
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)
    metric = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    calculated = Column(Boolean, default=False)
    formula = Column(String, nullable=True)

    # Print managing
    def __repr__(self):
        return f"Metric #{self.id} {self.metric} belongs to habit #{self.habit_id}"

# BADGES
class Badges(Base):
    __tablename__ = "badges"

    # Columns
    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)
    metric_id = Column(Integer, ForeignKey("metrics.id"), nullable=False)
    badge = Column(String, nullable=False)
    metric_type = Column(String, nullable=False)

    frequency_target = Column(Integer, nullable=True)
    frequency_period = Column(String, nullable=True)
    higher_is_better = Column(Boolean, default=True)

    unlocked = Column(Float, nullable=False)
    bronze = Column(Float, nullable=False)
    silver = Column(Float, nullable=False)
    gold = Column(Float, nullable=False)
    diamond = Column(Float, nullable=False)

    current_value = Column(Float, default=0)
    current_tier = Column(String, default="locked")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "unlocked < bronze AND "
            "bronze < silver AND "
            "silver < gold AND "
            "gold < diamond",
            name="tiers_check"
        ),
    )

    # Print managing
    def __repr__(self):
        return f"Badge #{self.id} {self.badge} belongs to habit #{self.habit_id} and current tier is {self.current_tier}"

# DATA ENTRY
class Entries(Base):
    __tablename__ = "entries"

    # Columns
    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)
    metric_id = Column(Integer, ForeignKey("metrics.id"), nullable=False)
    value = Column(Float, nullable=False)
    date = Column(Date, nullable=False)

    # Print managing
    def __repr__(self):
        return f"Entry #{self.id} on day {self.date} refers to habit #{self.habit_id} and metric #{self.metric_id} with value {self.value}."
