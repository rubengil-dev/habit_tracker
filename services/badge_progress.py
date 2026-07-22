"""
This page contains the necessary functions to re-calcule de badge's progress based on new/delete entries.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Badges, Entries
from services.utils import check_tier, count_entries_by_period

def calculation_router(db: Session, badge: Badges) -> tuple[float, str]:
    """Dispatches to the right calculation function based on the badge's metric_type."""

    if badge.metric_type == "historic":
        return calculate_historic(db, badge)
    elif badge.metric_type == "top":
        return calculate_top(db, badge)
    elif badge.metric_type == "objective":
        return calculate_objective(db, badge)
    elif badge.metric_type == "consistency":
        return calculate_consistency(db, badge)
    else:
        raise ValueError(f"Unknown metric_type: {badge.metric_type}")
    
# BADGE RECALCULATION
def recalculate_badges(db: Session, metric_id: int) -> list[dict]:
    """ 1. Finds every badge linked to a metric. 
        2. Recalculates.
        3. Saves new value and tier.
        4. Reports whether its tier changed."""
    
    # Obtains affected badges
    affected_badges = db.query(Badges).filter(Badges.metric_id == metric_id).all()
    results = []

    # For each badge, saves previous values and tiers and calculates new ones
    for badge in affected_badges:
        old_tier = badge.current_tier                                   
        new_value, new_tier = calculation_router(db, badge)

        # Saving new values
        badge.current_value = new_value
        badge.current_tier = new_tier

        # Necesary to know if tier changed
        results.append({
            "badge_id": badge.id,
            "current_value": new_value,
            "old_tier": old_tier,
            "new_tier": new_tier,
            "tier_changed": old_tier != new_tier
        })

    # DataBase Update
    db.commit()
    return results


def calculate_historic(db: Session, badge: Badges) -> tuple[float, str]:
    """Calculates the cumulative sum of a badge's entries and returns (value, tier)."""

    total = db.query(func.sum(Entries.value)).filter(Entries.metric_id == badge.metric_id).scalar()

    value = total or 0                 # Managing no entries
    tier = check_tier(badge, value)
    return value, tier

def calculate_top(db: Session, badge: Badges) -> tuple[float, str]:
    """Finds the best single-entry value for a metric (max or min depending on
    higher_is_better) and returns (value, tier)."""

    query = db.query(func.max(Entries.value)) if badge.higher_is_better else db.query(func.min(Entries.value))
    best = query.filter(Entries.metric_id == badge.metric_id).scalar()

    value = best or 0                 # Managing no entries
    tier = check_tier(badge, value)
    return value, tier

def calculate_objective(db: Session, badge: Badges) -> tuple[float, str]:
    """Counts how many entries of a metric passed the badge's threshold_value
    (or stayed below it, depending on higher_is_better), and returns (value, tier)."""
    query = db.query(func.count(Entries.id)).filter(Entries.metric_id == badge.metric_id)

    if badge.higher_is_better:
        query = query.filter(Entries.value >= badge.threshold_value)
    else:
        query = query.filter(Entries.value <= badge.threshold_value)

    value = query.scalar() or 0     # Managing no entries
    tier = check_tier(badge, value)
    return value, tier


def calculate_consistency(db: Session, badge: Badges) -> tuple[float, str]:
    """Counts how many periods (week/month/quarter/etc.) reached the badge's
    frequency_target, counting only entries that pass threshold_value (if set)."""

    # Calculates number of entries within a period
    counts = count_entries_by_period(
        db, badge.metric_id, badge.frequency_period,
        badge.threshold_value, badge.higher_is_better
    )

    value = sum(1 for count in counts.values() if count >= badge.frequency_target)
    tier = check_tier(badge, value)
    return value, tier