"""
This page contains the functions necessary to calcule streaks to show them on front.
"""

from datetime import date
from sqlalchemy import func
from sqlalchemy.orm import Session
from models import Badges, Entries
from services.utils import get_period, get_previous_period, get_period_bounds
from enums import FrequencyPeriod
from datetime import date
from collections import defaultdict

# Constant: Periods and their orders.
PERIOD_ORDER = [p.value for p in FrequencyPeriod]

# ------------------------- BADGES ------------------------- #

def current_badge_progress(badge: Badges, db: Session) -> tuple[int, int]:
    """Returns (current, target) progress for a consistency badge's CURRENT period.
       This is the functions that calcules the streak within a badge's period to display it."""

    # Get current period date bounds
    start, end = get_period_bounds(date.today(), badge.frequency_period)

    # Query preparation
    query = db.query(func.count(Entries.id)).filter(
    Entries.metric_id == badge.metric_id,
    Entries.date >= start,
    Entries.date <= end
    )

    # Threshold comparison to complete query
    if badge.threshold_value is not None:

        if badge.higher_is_better:
            query = query.filter(Entries.value >= badge.threshold_value)
        else:
            query = query.filter(Entries.value <= badge.threshold_value)

    # Query itself
    count = query.scalar() or 0

    return (count, badge.frequency_target)

# ------------------------- HABITS ------------------------- #

def get_active_consistency_badge(habit_id: int, db: Session) -> Badges | None:
    """Returns the consistency badge that drives the habit's streak indicator.
    Picks the badge with the shortest frequency_period; ties are broken by
    the highest frequency_target (the more demanding badge wins)."""

    # Query itself
    badges = db.query(Badges).filter(Badges.habit_id == habit_id, Badges.metric_type == "consistency").all()

    # Badges existence check
    if not badges:
        return None

    # Tie-break: Tuples comparison is made firstly, by first element, if still tie, then looks the second one:
    # So, first, tuples are compared for MIN f_period. If still tie, then are compared for MAX (-)f_target.
    return min(badges,key=lambda b: (PERIOD_ORDER.index(b.frequency_period), -b.frequency_target))

def calculate_habit_streak(habit_id: int, db: Session) -> int:
    """Calculates the CURRENT streak of consecutive fulfilled periods for a habit,
    based on its active consistency badge. The current period counts immediately if already fulfilled,
    but never breaks the streak if not yet fulfilled — only closed periods can break it."""

    # ActiveBadge existence check
    badge = get_active_consistency_badge(habit_id, db)

    if badge is None:
        return 0

    # Query preparation
    query = db.query(Entries).filter(Entries.metric_id == badge.metric_id)

    # Threshold comparison
    if badge.threshold_value is not None:
        if badge.higher_is_better:
            query = query.filter(Entries.value >= badge.threshold_value)
        else:
            query = query.filter(Entries.value <= badge.threshold_value)

    # Query itself
    entries = query.all()

    # Group entries by period
    counts = defaultdict(int)

    for entry in entries:
        key = get_period(entry.date, badge.frequency_period)
        counts[key] += 1

    # Streak calculation, walking backwards period by period
    streak = 0
    cursor = date.today()
    first_period = True

    while True:
        key = get_period(cursor, badge.frequency_period)
        fulfilled = counts[key] >= badge.frequency_target

        # Sum 1 if CURRENT period is already fulfilled
        if first_period:
            first_period = False

            if fulfilled:
                streak += 1
            
            # If not fulfilled yet, skip (no break, no sum)

        # Sum 1 if PREVIOUS period is already fulfilled, breaks if not
        else:
            if fulfilled:
                streak += 1

            else:
                break

        cursor = get_previous_period(cursor, badge.frequency_period)

    return streak