"""
Badge tiers:
    - Tier of a value, going up or down
    - No value yet is locked (v1 bug 3)
    - Suggested thresholds
"""

# Imports
import pytest

from app.enums import BadgeKind, Tier
from app.services.tiers import is_count, suggest_tiers, tier_for
from tests.helpers import make_badge

# Pace in seconds per km: lower is better
DESCENDING = dict(unlocked=400, bronze=360, silver=330, gold=300, diamond=270)


@pytest.mark.parametrize(("value", "tier"), [
    (0,     Tier.LOCKED),
    (1,     Tier.UNLOCKED),
    (7,     Tier.BRONZE),
    (10,    Tier.SILVER),
    (100,   Tier.DIAMOND),
    (1000,  Tier.DIAMOND),
])
def test_tier_going_up(value, tier):
    """Higher is better: each threshold is reached from below."""
    assert tier_for(make_badge(kind=BadgeKind.HISTORIC), value) == tier


@pytest.mark.parametrize(("value", "tier"), [
    (450,   Tier.LOCKED),
    (400,   Tier.UNLOCKED),
    (340,   Tier.BRONZE),
    (300,   Tier.GOLD),
    (250,   Tier.DIAMOND),
])
def test_tier_going_down(value, tier):
    """Lower is better (record of pace): each threshold is reached from above."""
    badge = make_badge(kind=BadgeKind.RECORD, higher_is_better=False, **DESCENDING)
    assert tier_for(badge, value) == tier


def test_no_value_is_locked():
    """v1 bug 3: a lower-is-better record with no sessions came out as diamond."""
    badge = make_badge(kind=BadgeKind.RECORD, higher_is_better=False, **DESCENDING)
    assert tier_for(badge, None) == Tier.LOCKED


def test_counts_always_go_up():
    """An objective on pace counts sessions under the bar: more sessions, higher tier."""
    badge = make_badge(kind=BadgeKind.OBJECTIVE, higher_is_better=False, threshold=300)
    assert tier_for(badge, 12) == Tier.SILVER


@pytest.mark.parametrize(("first", "diamond", "tiers"), [
    (100,   100000, [100, 500, 3000, 20000, 100000]),       # Km run
    (1,     100,    [1, 3, 10, 30, 100]),                   # Sessions
    (1,     30,     [1, 2, 5, 10, 30]),                     # Days in a row
    (400,   270,    [400, 360, 330, 300, 270]),             # Pace, lower is better
    (0.5,   0.1,    [0.5, 0.33, 0.22, 0.15, 0.1]),          # Decimals, lower is better
])
def test_suggested_tiers(first, diamond, tiers):
    """Exponential progression, rounded to friendly numbers while it stays in order."""
    assert suggest_tiers(first, diamond) == tiers


def test_suggested_tiers_stay_in_order_in_narrow_ranges():
    """When friendly numbers would repeat, less rounding: 5 → 10 still gives five different thresholds."""
    tiers = suggest_tiers(5, 10)

    assert tiers[0] == 5 and tiers[-1] == 10
    assert tiers == sorted(set(tiers))


@pytest.mark.parametrize(("first", "diamond"), [(0, 100), (-5, 100), (100, 100)])
def test_suggested_tiers_need_valid_ends(first, diamond):
    """Both ends positive and different."""
    with pytest.raises(ValueError):
        suggest_tiers(first, diamond)


@pytest.mark.parametrize(("first", "diamond", "tiers"), [
    (1,     5,      [1, 2, 3, 4, 5]),                       # Tight: nudged apart
    (1,     7,      [1, 2, 3, 5, 7]),
    (1,     365,    [1, 5, 20, 100, 365]),                  # Days in a year
    (2,     12,     [2, 3, 5, 10, 12]),
])
def test_suggested_whole_tiers(first, diamond, tiers):
    """Counts: whole numbers only, friendly where they fit."""
    assert suggest_tiers(first, diamond, whole=True) == tiers


@pytest.mark.parametrize(("first", "diamond"), [(1, 4), (1.5, 10), (10, 1)])
def test_suggested_whole_tiers_need_room_whole_ends_and_going_up(first, diamond):
    """No room for five whole numbers, decimal ends, or going down → ValueError."""
    with pytest.raises(ValueError):
        suggest_tiers(first, diamond, whole=True)


@pytest.mark.parametrize(("fields", "count"), [
    (dict(kind=BadgeKind.HISTORIC),                         True),
    (dict(kind=BadgeKind.HISTORIC, metric_id=1),            False),
    (dict(kind=BadgeKind.RECORD, metric_id=1),              False),
    (dict(kind=BadgeKind.OBJECTIVE, metric_id=1),           True),
    (dict(kind=BadgeKind.CONSISTENCY),                      True),
    (dict(kind=BadgeKind.STREAK),                           True),
])
def test_which_badges_are_counts(fields, count):
    """Counts: sessions, objectives and periods; metric sums and records are not."""
    assert is_count(make_badge(**fields)) is count
