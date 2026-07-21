from enums import Tier
from datetime import date, timedelta
from models import Badges

def check_tier(badge: Badges, value: float) -> str:
    """Compares a value against a badge's thresholds and returns the matching tier."""

    # Logic for when a higher value is better
    if badge.higher_is_better:
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
    
    # Logic for when a lower value is better
    else:
        if value > badge.unlocked:
            return Tier.LOCKED
        elif value <= badge.diamond:
            return Tier.DIAMOND
        elif value <= badge.gold:
            return Tier.GOLD
        elif value <= badge.silver:
            return Tier.SILVER
        elif value <= badge.bronze:
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
    
def get_previous_period(cursor_date: date, frequency_period: str) -> date:
    """Returns a date that falls inside the period immediately before the one
    containing cursor_date. Meant to be chained with get_period to walk backwards
    period by period (used by the habit streak calculation)."""

    if frequency_period == "daily":
        return cursor_date - timedelta(days=1)

    elif frequency_period == "weekly":
        return cursor_date - timedelta(days=7)

    elif frequency_period == "monthly":
        first_day_of_month = cursor_date.replace(day=1)
        return first_day_of_month - timedelta(days=1)

    elif frequency_period == "quarterly":
        quarter_start_month = ((cursor_date.month - 1) // 3) * 3 + 1
        first_day_of_quarter = cursor_date.replace(month=quarter_start_month, day=1)
        return first_day_of_quarter - timedelta(days=1)

    elif frequency_period == "halfyearly":
        half_start_month = 1 if cursor_date.month <= 6 else 7
        first_day_of_half = cursor_date.replace(month=half_start_month, day=1)
        return first_day_of_half - timedelta(days=1)

    elif frequency_period == "yearly":
        first_day_of_year = cursor_date.replace(month=1, day=1)
        return first_day_of_year - timedelta(days=1)

    else:
        raise ValueError(f"Unknown frequency_period: {frequency_period}")
    
def get_period_bounds(cursor_date: date, frequency_period: str) -> tuple[date, date]:
    """Returns (start_date, end_date) of the natural period containing cursor_date.
    Built entirely on top of get_previous_period to save code and possible errors."""

    # DAY1 of this period
    start = get_previous_period(cursor_date, frequency_period) + timedelta(days=1)

    # LAST DAY of this period
    end = start
    while get_period(end + timedelta(days=1), frequency_period) == get_period(start, frequency_period):
        end += timedelta(days=1)

    return start, end