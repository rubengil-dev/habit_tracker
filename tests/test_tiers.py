"""
Badge tiers:
    - Tier of a value, going up or down
    - No value yet is locked (v1 bug 3)
    - Suggested thresholds
    - Random ends and values: suggestions always valid, tiers never go backwards
"""

# Imports
import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from app.enums import BadgeKind, Tier
from app.services.tiers import is_count, suggest_tiers, tier_for
from tests.helpers import make_badge

# Random positive ends, from tiny decimals to millions
ENDS = st.floats(min_value=0.001, max_value=1e7, allow_nan=False, allow_infinity=False)

# Tiers from worst to best
TIER_RANK = list(Tier)

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


@pytest.mark.parametrize(("first", "diamond"), [(0, 100), (-5, 100), (100, 100), (1e7, 9999999.999999998)])
def test_suggested_tiers_need_valid_ends(first, diamond):
    """Both ends positive, different, and not so close that the thresholds in between repeat (found by the random test)."""
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


# Random ends and values

@given(first=ENDS, diamond=ENDS)
def test_suggested_tiers_always_valid(first, diamond):
    """Any two different positive ends → five thresholds, ends kept, strictly in order; or, if they are almost equal, ValueError."""
    assume(first != diamond)
    try:
        tiers = suggest_tiers(first, diamond)
    except ValueError:
        assert abs(diamond - first) < 1e-12 * max(first, diamond)
        return

    assert len(tiers) == 5 and (tiers[0], tiers[-1]) == (first, diamond)
    assert tiers == sorted(set(tiers), reverse=first > diamond)


@given(first=st.integers(1, 10_000), room=st.integers(4, 1_000_000))
def test_suggested_whole_tiers_always_valid(first, room):
    """Whole ends with room for five → five different whole numbers going up, ends kept."""
    tiers = suggest_tiers(float(first), float(first + room), whole=True)

    assert (tiers[0], tiers[-1]) == (first, first + room)
    assert all(tier.is_integer() for tier in tiers)
    assert tiers == sorted(set(tiers))


@given(low=st.floats(0, 1000), high=st.floats(0, 1000), higher_is_better=st.booleans())
def test_better_value_never_lower_tier(low, high, higher_is_better):
    """A better value never gets a lower tier, going up or down."""
    assume(low <= high)
    tiers = DESCENDING if not higher_is_better else dict(unlocked=1, bronze=5, silver=10, gold=50, diamond=100)
    badge = make_badge(kind=BadgeKind.RECORD, metric_id=1, higher_is_better=higher_is_better, **tiers)
    worse, better = (low, high) if higher_is_better else (high, low)

    assert TIER_RANK.index(tier_for(badge, better)) >= TIER_RANK.index(tier_for(badge, worse))
