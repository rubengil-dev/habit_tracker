"""
Badge tiers:
    - Tier reached by a value
    - Suggested thresholds between the first one and diamond
"""

# Imports
import math

from app.enums import BadgeKind, Tier
from app.models import Badge

# Friendly roundings: 1, 2, 3 or 5 times a power of ten
FRIENDLY_STEPS = (1, 2, 3, 5, 10)


# Tier of a value

def tier_for(badge: Badge, value: float | None) -> Tier:
    """Tier reached by a value; no value yet → locked."""
    if value is None:
        return Tier.LOCKED

    thresholds = [
        (Tier.DIAMOND,  badge.diamond),
        (Tier.GOLD,     badge.gold),
        (Tier.SILVER,   badge.silver),
        (Tier.BRONZE,   badge.bronze),
        (Tier.UNLOCKED, badge.unlocked),
    ]
    for tier, threshold in thresholds:
        if reaches(value, threshold, is_descending(badge)):
            return tier

    return Tier.LOCKED


def is_descending(badge: Badge) -> bool:
    """Lower is better only in historic and record; counts always go up."""
    return badge.kind in (BadgeKind.HISTORIC, BadgeKind.RECORD) and not badge.higher_is_better


def reaches(value: float, threshold: float, descending: bool) -> bool:
    """Whether a value reaches a threshold, in the badge's direction."""
    return value <= threshold if descending else value >= threshold


# Suggested thresholds

def suggest_tiers(first: float, diamond: float) -> list[float]:
    """
    Suggested thresholds, unlocked to diamond:
        - Exponential progression between the two ends, which are kept as typed
        - The three in between, rounded as much as possible while they stay in order
        Example: 100, 100000 → [100, 500, 3000, 20000, 100000]
    """
    if first <= 0 or diamond <= 0 or first == diamond:
        raise ValueError("Both ends must be positive and different")

    middle = exponential_steps(first, diamond)

    for rounding in (round_friendly, round_two_figures, round_four_figures):
        tiers = [first, *(rounding(value) for value in middle), diamond]
        if in_order(tiers):
            return tiers

    return [first, *middle, diamond]


def exponential_steps(first: float, diamond: float) -> list[float]:
    """The three thresholds in between, each one the previous times the same factor."""
    factor = (diamond / first) ** (1 / 4)
    return [first * factor ** step for step in (1, 2, 3)]


def round_friendly(value: float) -> float:
    """Nearest friendly number (1, 2, 3 or 5 times a power of ten), compared in proportion."""
    power = 10 ** math.floor(math.log10(value))
    candidates = [clean(step * power) for step in FRIENDLY_STEPS]
    return min(candidates, key=lambda candidate: abs(math.log(candidate / value)))


def round_two_figures(value: float) -> float:
    """Rounded to two significant figures: 562 → 560."""
    return clean(float(f"{value:.2g}"))


def round_four_figures(value: float) -> float:
    """Rounded to four significant figures: 5.9461 → 5.946."""
    return clean(float(f"{value:.4g}"))


def clean(value: float) -> float:
    """Float noise remover: 0.30000000000000004 → 0.3."""
    return float(f"{value:.12g}")


def in_order(tiers: list[float]) -> bool:
    """Strictly going up, or strictly going down, all the way from the first to diamond."""
    pairs = list(zip(tiers, tiers[1:]))
    if tiers[0] < tiers[-1]:
        return all(low < high for low, high in pairs)
    return all(high > low for high, low in pairs)
