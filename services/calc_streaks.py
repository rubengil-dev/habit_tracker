"""
Streaks and progress:
    - Progress of a consistency badge in the current period
    - Streak of a habit
"""

# Imports
from datetime import date
from sqlalchemy import func
from sqlalchemy.orm import Session

from enums import FrequencyPeriod
from models import Badges, Entries
from services.utils import get_period, get_previous_period, get_period_bounds, count_entries_by_period

# Period order: shortest first, as declared in FrequencyPeriod
PERIOD_ORDER = [p.value for p in FrequencyPeriod]

# Badges

def current_badge_progress(badge: Badges, db: Session) -> tuple[int, int]:
    """Progress of a consistency badge in the current period → (current, target)."""

    # Current period
    start, end = get_period_bounds(date.today(), badge.frequency_period)

    # Query
    query = db.query(func.count(Entries.id)).filter(
    Entries.metric_id == badge.metric_id,
    Entries.date >= start,
    Entries.date <= end
    )

    # Threshold filter
    if badge.threshold_value is not None:

        if badge.higher_is_better:
            query = query.filter(Entries.value >= badge.threshold_value)
        else:
            query = query.filter(Entries.value <= badge.threshold_value)

    # Count
    count = query.scalar() or 0

    return (count, badge.frequency_target)

# Habits

def get_active_consistency_badge(habit_id: int, db: Session) -> Badges | None:
    """
    Active consistency badge finder:
        - Shortest frequency_period wins
        - Ties: highest frequency_target wins
    """

    # Query
    badges = db.query(Badges).filter(Badges.habit_id == habit_id, Badges.metric_type == "consistency").all()

    # Existence check
    if not badges:
        return None

    # Tuples compare element by element: shortest period first, then highest target (negated)
    return min(badges,key=lambda b: (PERIOD_ORDER.index(b.frequency_period), -b.frequency_target))

def calculate_habit_streak(habit_id: int, db: Session) -> int:
    """
    Current streak of a habit, from its active consistency badge:
        - Counts consecutive fulfilled periods, backwards from the current one
        - Current period counts if fulfilled, but never breaks the streak
    """

    # Active badge check
    badge = get_active_consistency_badge(habit_id, db)

    if badge is None:
        return 0

    # Entries per period
    counts = count_entries_by_period(
        db, badge.metric_id, badge.frequency_period,
        badge.threshold_value, badge.higher_is_better
        )

    # Walk backwards
    streak = 0
    cursor = date.today()
    first_period = True

    while True:
        key = get_period(cursor, badge.frequency_period)
        fulfilled = counts[key] >= badge.frequency_target

        # Current period: counts if fulfilled, otherwise skipped
        if first_period:
            first_period = False

            if fulfilled:
                streak += 1

        # Previous periods: count if fulfilled, otherwise break
        else:
            if fulfilled:
                streak += 1

            else:
                break

        cursor = get_previous_period(cursor, badge.frequency_period)

    return streak
