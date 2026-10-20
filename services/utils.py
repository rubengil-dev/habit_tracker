"""
Domain-blind helpers:
    - Tier lookup
    - Natural calendar periods
    - Entries count per period
"""

# Imports
from datetime import date, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session

from enums import Tier
from models import Badges, Entries


def check_tier(badge: Badges, value: float) -> str:
    """Tier finder: compares a value against the badge's thresholds."""

    # Counts (consistency, objective) are always ascending
    ascending = badge.higher_is_better or badge.metric_type in ("consistency", "objective")

    # Ascending tiers
    if ascending:
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

    # Descending tiers
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

def count_entries_by_period(db: Session, metric_id: int, frequency_period: str,
                             threshold_value: float | None = None,
                             higher_is_better: bool = True) -> dict[str, int]:
    """Entries counter per period, applying the threshold filter if set."""

    # Query
    query = db.query(Entries.date).filter(Entries.metric_id == metric_id)

    # Threshold filter
    if threshold_value is not None:
        if higher_is_better:
            query = query.filter(Entries.value >= threshold_value)
        else:
            query = query.filter(Entries.value <= threshold_value)

    # Count
    counts = defaultdict(int)
    for (entry_date,) in query.all():
        key = get_period(entry_date, frequency_period)
        counts[key] += 1

    return counts

def get_period(entry_date: date, frequency_period: str) -> tuple:
    """Period key finder: date → key of its natural period."""

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
    """Previous period finder: date → a date inside the period before its own."""

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
    """Period bounds finder: date → (first day, last day) of its natural period."""

    # Start
    start = get_previous_period(cursor_date, frequency_period) + timedelta(days=1)

    # End
    end = start
    while get_period(end + timedelta(days=1), frequency_period) == get_period(start, frequency_period):
        end += timedelta(days=1)

    return start, end
