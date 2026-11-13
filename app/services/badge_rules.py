"""
Rules a badge must follow, whatever the format it comes in (API body or table row):
    - Fields each kind needs, and none it does not use
    - Tag filters that fit together
    - Thresholds in the badge's direction, whole in counts
    - Metrics each kind can use
Each rule raises ValueError with what is wrong.
"""

# Imports
from itertools import pairwise

from app.enums import BadgeKind, GoalMode, MetricKind
from app.services.tiers import is_count, is_descending

# Badge kinds with a period goal, and with a bar on a metric
PERIODIC = (BadgeKind.CONSISTENCY, BadgeKind.STREAK)
WITH_BAR = (BadgeKind.OBJECTIVE, BadgeKind.CONSISTENCY, BadgeKind.STREAK)


def check_badge(badge):
    """Every rule that only needs the badge's own fields."""
    check_kind_fields(badge)
    check_tag_filters(badge)
    check_tiers(badge)


def check_kind_fields(badge):
    """Fields each badge kind needs, and none it does not use."""
    kind = badge.kind
    goal = (badge.period, badge.target, badge.mode)

    if kind == BadgeKind.RECORD and badge.metric_id is None:
        raise ValueError("A record needs a metric")
    if kind == BadgeKind.OBJECTIVE and (badge.metric_id is None or badge.threshold is None):
        raise ValueError("An objective needs a metric and a threshold")
    if kind in PERIODIC and None in goal:
        raise ValueError("Consistency and streak badges need period, target and mode")
    if kind not in PERIODIC and goal != (None, None, None):
        raise ValueError("Only consistency and streak badges have period, target and mode")
    if kind not in WITH_BAR and badge.threshold is not None:
        raise ValueError("Only objective, consistency and streak badges have a threshold")
    if kind in PERIODIC and (badge.metric_id is None) != (badge.threshold is None):
        raise ValueError("In consistency and streak badges, a metric comes with a threshold")
    if kind == BadgeKind.HISTORIC and not badge.higher_is_better:
        raise ValueError("A historic badge is a sum, which only goes up: higher_is_better must be true")
    if badge.target == 0 and badge.mode == GoalMode.MIN:
        raise ValueError("A goal of at least 0 is always met: use at least 1, or at most 0")


def check_tag_filters(badge):
    """Untagged only, or tag rules; each tag once."""
    tag_ids = badge.required_tag_ids + badge.excluded_tag_ids

    if badge.untagged_only and tag_ids:
        raise ValueError("An untagged-only badge cannot require or exclude tags")
    if len(set(tag_ids)) != len(tag_ids):
        raise ValueError("Each tag can appear only once, as required or as excluded")


def check_tiers(badge):
    """Thresholds strictly in the badge's direction, from unlocked to diamond, and whole in counts."""
    tiers = [badge.unlocked, badge.bronze, badge.silver, badge.gold, badge.diamond]
    pairs = list(pairwise(tiers))

    if is_count(badge) and not all(tier.is_integer() for tier in tiers):
        raise ValueError("This badge counts sessions or periods: its thresholds must be whole numbers")
    if is_descending(badge) and not all(high > low for high, low in pairs):
        raise ValueError("Lower is better: thresholds must go down from unlocked to diamond")
    if not is_descending(badge) and not all(low < high for low, high in pairs):
        raise ValueError("Thresholds must go up from unlocked to diamond")


def check_metric_fits(kind: BadgeKind, metric_kind: MetricKind):
    """A historic badge adds its metric up: a sum of ratios (paces) means nothing."""
    if kind == BadgeKind.HISTORIC and metric_kind == MetricKind.RATIO:
        raise ValueError("A historic badge adds its metric up, and a sum of ratios means nothing: use a record or an objective")
