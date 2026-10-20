"""
Badge recalculation:
    - Dispatcher by metric type
    - One calculation per metric type
"""

# Imports
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import Badges, Entries
from services.utils import check_tier, count_entries_by_period


def calculation_router(db: Session, badge: Badges) -> tuple[float, str]:
    """Dispatcher: badge → calculation of its metric_type."""

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

def recalculate_badges(db: Session, metric_id: int) -> list[dict]:
    """
    Badges recalculation of a metric:
        - Saves the new value and tier of every badge linked to it
        - Reports whether each tier changed
    """

    # Affected badges
    affected_badges = db.query(Badges).filter(Badges.metric_id == metric_id).all()
    results = []

    # Recalculation
    for badge in affected_badges:
        old_tier = badge.current_tier
        new_value, new_tier = calculation_router(db, badge)

        # Save
        badge.current_value = new_value
        badge.current_tier = new_tier

        # Report
        results.append({
            "badge_id": badge.id,
            "current_value": new_value,
            "old_tier": old_tier,
            "new_tier": new_tier,
            "tier_changed": old_tier != new_tier
        })

    # Commit
    db.commit()
    return results


def calculate_historic(db: Session, badge: Badges) -> tuple[float, str]:
    """Sum of every entry of the metric → (value, tier)."""

    total = db.query(func.sum(Entries.value)).filter(Entries.metric_id == badge.metric_id).scalar()

    value = total or 0                 # No entries → 0
    tier = check_tier(badge, value)
    return value, tier

def calculate_top(db: Session, badge: Badges) -> tuple[float, str]:
    """Best entry of the metric (max or min by higher_is_better) → (value, tier)."""

    query = db.query(func.max(Entries.value)) if badge.higher_is_better else db.query(func.min(Entries.value))
    best = query.filter(Entries.metric_id == badge.metric_id).scalar()

    value = best or 0                 # No entries → 0
    tier = check_tier(badge, value)
    return value, tier

def calculate_objective(db: Session, badge: Badges) -> tuple[float, str]:
    """Entries of the metric that pass threshold_value, counted → (value, tier)."""

    query = db.query(func.count(Entries.id)).filter(Entries.metric_id == badge.metric_id)

    if badge.higher_is_better:
        query = query.filter(Entries.value >= badge.threshold_value)
    else:
        query = query.filter(Entries.value <= badge.threshold_value)

    value = query.scalar() or 0     # No entries → 0
    tier = check_tier(badge, value)
    return value, tier


def calculate_consistency(db: Session, badge: Badges) -> tuple[float, str]:
    """
    Periods that reached frequency_target, counted → (value, tier):
        - Only entries that pass threshold_value count, if set
    """

    # Entries per period
    counts = count_entries_by_period(
        db, badge.metric_id, badge.frequency_period,
        badge.threshold_value, badge.higher_is_better
    )

    value = sum(1 for count in counts.values() if count >= badge.frequency_target)
    tier = check_tier(badge, value)
    return value, tier
