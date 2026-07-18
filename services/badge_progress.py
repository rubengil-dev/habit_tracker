from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Badges, Entries
from enums import Tier

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

    value = query.scalar() or 0
    tier = check_tier(badge, value)
    return value, tier


def calculate_consistency(db: Session, badge: Badges) -> tuple[float, str]:
    """ TODO """
    
    # TODO
    pass