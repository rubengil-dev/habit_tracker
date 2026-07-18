"""
This script creates every Enum needed for Pydantic models.
"""

from enum import Enum

# METRICS
class MetricType(str, Enum):
    HISTORIC = "historic"           # For Whole-Time metrics        : You've run 157 km
    TOP = "top"                     # Only records the Best time    : Best pace is 4,56''
    OBJECTIVE = "objective"         # For goal achievements         : Run 10+ KM in one run
    CONSISTENCY = "consistency"     # For periods consistency       : Read every day in a week

# TIERS
class Tier(str, Enum):
    LOCKED = "locked"               # Not done a single time
    UNLOCKED = "unlocked"           # Done at least one
    BRONZE = "bronze"               # Easy
    SILVER = "silver"               # Medium
    GOLD = "gold"                   # Hard
    DIAMOND = "diamond"             # Extreme

# FREQUENCY PERIOD
class FrequencyPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    HALFYEARLY = "halfyearly"
    YEARLY = "yearly"