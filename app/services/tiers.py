"""
Badge tiers:
    - Tier reached by a value
    - Suggested thresholds between the first one and diamond
"""

# Imports
import math
from itertools import pairwise

from app.enums import BadgeKind, Tier
from app.models import Badge
from app.utils.numbers import drop_float_noise

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
    """Lower is better only in records; sums and counts always go up."""
    return badge.kind == BadgeKind.RECORD and not badge.higher_is_better


def is_count(badge: Badge) -> bool:
    """Value counts sessions or periods, so its thresholds are whole numbers: every kind but metric sums and records."""
    if badge.kind == BadgeKind.HISTORIC:
        return badge.metric_id is None
    return badge.kind != BadgeKind.RECORD


def reaches(value: float, threshold: float, descending: bool) -> bool:
    """Whether a value reaches a threshold, in the badge's direction."""
    return value <= threshold if descending else value >= threshold


# Suggested thresholds

def suggest_tiers(first: float, diamond: float, whole: bool = False) -> list[float]:
    """
    Suggested thresholds, unlocked to diamond:
        - Exponential progression between the two ends, which are kept as typed
        - The three in between, rounded as much as possible while they stay in order
        - whole: only whole numbers, for badges that count sessions or periods
        - Ends so close that the thresholds in between would repeat → ValueError
        Example: 100, 100000 → [100, 500, 3000, 20000, 100000]
    """
    if first <= 0 or diamond <= 0 or first == diamond:
        raise ValueError("Both ends must be positive and different")

    middle = exponential_steps(first, diamond)

    if whole:
        return whole_tiers(first, diamond, middle)

    for rounding in (round_friendly, round_two_figures, round_four_figures, float):
        tiers = [first, *(rounding(value) for value in middle), diamond]
        if in_order(tiers):
            return tiers

    raise ValueError(f"{first:g} and {diamond:g} are too close for five different thresholds")


def whole_tiers(first: float, diamond: float, middle: list[float]) -> list[float]:
    """
    Whole thresholds, going up:
        - Friendly numbers if they stay in order; otherwise the nearest whole numbers, nudged apart
        Example: 1, 5 → [1, 2, 3, 4, 5]
    """
    if not (first.is_integer() and diamond.is_integer()):
        raise ValueError("Both ends must be whole numbers")
    if first > diamond:
        raise ValueError("Counts always go up: the first threshold must be below diamond")
    if diamond - first < 4:
        raise ValueError(f"There is no room for five different whole thresholds between {first:g} and {diamond:g}")

    for rounding in (round_friendly, round_two_figures):
        tiers = [first, *(float(round(rounding(value))) for value in middle), diamond]
        if in_order(tiers):
            return tiers

    return nudged_apart([first, *(float(round(value)) for value in middle), diamond])


def exponential_steps(first: float, diamond: float) -> list[float]:
    """The three thresholds in between, each one the previous times the same factor."""
    factor = (diamond / first) ** (1 / 4)
    return [first * factor ** step for step in (1, 2, 3)]


def round_friendly(value: float) -> float:
    """Nearest friendly number (1, 2, 3 or 5 times a power of ten), compared in proportion."""
    power = 10 ** math.floor(math.log10(value))
    candidates = [drop_float_noise(step * power) for step in FRIENDLY_STEPS]
    return min(candidates, key=lambda candidate: abs(math.log(candidate / value)))


def round_two_figures(value: float) -> float:
    """Rounded to two significant figures: 562 → 560."""
    return drop_float_noise(float(f"{value:.2g}"))


def round_four_figures(value: float) -> float:
    """Rounded to four significant figures: 5.9461 → 5.946."""
    return drop_float_noise(float(f"{value:.4g}"))


def nudged_apart(tiers: list[float]) -> list[float]:
    """Whole thresholds going up, each at least 1 above the one before and 1 below the one after; both ends kept."""
    for i in range(1, 4):
        tiers[i] = max(tiers[i], tiers[i - 1] + 1)
    for i in range(3, 0, -1):
        tiers[i] = min(tiers[i], tiers[i + 1] - 1)
    return tiers


def in_order(tiers: list[float]) -> bool:
    """Strictly going up, or strictly going down, all the way from the first to diamond."""
    pairs = list(pairwise(tiers))
    if tiers[0] < tiers[-1]:
        return all(low < high for low, high in pairs)
    return all(high > low for high, low in pairs)
