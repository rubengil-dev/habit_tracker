"""
This script creates every Pydantic model needed
"""

from enum import Enum

# METRICS
class MetricType(str, Enum):
    HISTORIC = "historic"
    TOP = "top"
    OBJECTIVE = "objective"
    CONSISTENCY = "consistency"

# TIERS
class Tier(str, Enum):
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    DIAMOND = "diamond"