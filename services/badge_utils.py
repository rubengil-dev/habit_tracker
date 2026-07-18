from enums import Tier
from datetime import date
from models import Badges

def check_tier(badge: Badges, value: float) -> str:
    """Compares a value against a badge's thresholds and returns the matching tier."""
    if value < badge.unlocked:
        return Tier.LOCKED
    elif value >= badge.diamond:
        return Tier.DIAMOND
    elif value >= badge.gold:
        return Tier.GOLD
    elif value >= badge.silver:
        return Tier.SILVER
    elif value >= badge.bronze:
        return Tier.BRONZE
    else:
        return Tier.UNLOCKED
    
def get_period(entry_date: date, frequency_period: str) -> tuple:
    """Converts a date into a group key according to the given frequency_period,
    so entries falling in the same natural period share the same key."""

    if frequency_period == "daily":
        return (entry_date.year, entry_date.month, entry_date.day)
    elif frequency_period == "weekly":
        iso_year, iso_week, _ = entry_date.isocalendar()
        return (iso_year, iso_week)
    elif frequency_period == "monthly":
        return (entry_date.year, entry_date.month)
    elif frequency_period == "quarterly":
        quarter = (entry_date.month - 1) // 3
        return (entry_date.year, quarter)
    elif frequency_period == "halfyearly":
        half = (entry_date.month - 1) // 6
        return (entry_date.year, half)
    elif frequency_period == "yearly":
        return (entry_date.year,)
    else:
        raise ValueError(f"Unknown frequency_period: {frequency_period}")