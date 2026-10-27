"""
Enums shared by models, schemas and services.
"""

# Imports
from enum import Enum

# Metric kinds
class MetricKind(str, Enum):
    NUMBER = "number"               # Typed in
    DURATION = "duration"           # Typed in, stored in seconds
    RATIO = "ratio"                 # Calculated, A ÷ B

# Badge kinds
class BadgeKind(str, Enum):
    HISTORIC = "historic"           # Sum of a metric or sessions   : You've run 157 km
    RECORD = "record"               # Best value in one session     : Best pace is 4'56''
    OBJECTIVE = "objective"         # Sessions that pass a bar      : Run 10+ km in one run
    CONSISTENCY = "consistency"     # Periods that meet a target    : Read every day in a week
    STREAK = "streak"               # Consecutive periods (best)    : 4 weeks running 3 times a week

# Tiers
class Tier(str, Enum):
    LOCKED = "locked"               # Not done a single time
    UNLOCKED = "unlocked"           # Done at least one
    BRONZE = "bronze"               # Easy
    SILVER = "silver"               # Medium
    GOLD = "gold"                   # Hard
    DIAMOND = "diamond"             # Extreme

# Natural calendar periods
class Period(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    HALFYEARLY = "halfyearly"
    YEARLY = "yearly"

# Target direction
class GoalMode(str, Enum):
    MIN = "min"                     # At least n sessions           : gym 3 times a week
    MAX = "max"                     # At most n sessions (avoid)    : 0 cigarettes a day

# How a badge uses a tag
class TagRule(str, Enum):
    REQUIRED = "required"           # Session counts only with it   : run despite the rain
    EXCLUDED = "excluded"           # Session counts only without it: run with no pain
