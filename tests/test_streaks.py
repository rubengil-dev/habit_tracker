"""
Streaks of a habit, from its goal:
    - At least n: the current period adds once met and never breaks
    - At most n (avoid): the current period adds only when it closes, and breaks as soon as it goes over
    - Bounded by the start date (v1 bug 4) and retroactive when the goal changes
    - Random outcomes and sessions: same streaks as a plain count, and one more session never moves them the wrong way
"""

# Imports
import datetime as dt
from hypothesis import given
from hypothesis import strategies as st

from app.enums import GoalMode, Period
from app.services.streaks import Outcome, habit_streaks, streaks
from tests.helpers import facts, make_habit

# Random session days, between the habit's start (1/10/2026) and TODAY
SESSION_DAYS = st.lists(st.dates(min_value=dt.date(2026, 10, 1), max_value=dt.date(2026, 10, 26)), max_size=40)

# Monday
TODAY = dt.date(2026, 10, 26)


def days(first: int, last: int, month: int = 10) -> list[dt.date]:
    """Every day from first to last of a month of 2026."""
    return [dt.date(2026, month, day) for day in range(first, last + 1)]


def streaks_of(dates: list[dt.date], **goal) -> tuple[int, int]:
    """Current and best streak of a habit with those session dates."""
    defaults = dict(start_date=dt.date(2026, 10, 1), goal_target=1, goal_period=Period.DAILY)
    habit = make_habit(**(defaults | goal))
    return habit_streaks(habit, [facts(day) for day in dates], TODAY)


# At least n

def test_today_pending_does_not_break():
    """Done every day until yesterday, not yet today: the streak holds."""
    assert streaks_of(days(20, 25)) == (6, 6)


def test_today_adds_once_met():
    """Done today too: one more."""
    assert streaks_of(days(20, 26)) == (7, 7)


def test_gap_breaks_and_best_remains():
    """Ten days, a gap on the 20th, five more: current 5, best 10."""
    assert streaks_of(days(10, 19) + days(21, 25)) == (5, 10)


def test_weekly_goal():
    """Three times a week: two full weeks; this week (1 of 3 so far) is still open."""
    dates = [dt.date(2026, 10, 13), dt.date(2026, 10, 15), dt.date(2026, 10, 17),
             dt.date(2026, 10, 19), dt.date(2026, 10, 20), dt.date(2026, 10, 25),
             dt.date(2026, 10, 26)]
    assert streaks_of(dates, goal_target=3, goal_period=Period.WEEKLY) == (2, 2)


def test_two_sessions_on_one_day_count_apart():
    """Twice a day: two sessions on the same day meet it."""
    dates = [dt.date(2026, 10, 25), dt.date(2026, 10, 25)]
    assert streaks_of(dates, goal_target=2, start_date=dt.date(2026, 10, 25)) == (1, 1)


def test_goal_change_is_retroactive():
    """The same history judged by a new goal: once a day gives 4, twice a day gives 3."""
    dates = days(22, 25) + days(23, 25)
    start = dict(start_date=dt.date(2026, 10, 22))

    assert streaks_of(dates, **start) == (4, 4)
    assert streaks_of(dates, goal_target=2, **start) == (3, 3)


# At most n (avoid)

def test_avoid_counts_clean_days_since_start():
    """v1 bug 4: with no sessions, the streak stops at the start date instead of walking back forever."""
    avoid = dict(goal_target=0, goal_mode=GoalMode.MAX, start_date=dt.date(2026, 10, 20))
    assert streaks_of([], **avoid) == (6, 6)


def test_avoid_slip_today_breaks_at_once():
    """A session today goes over "at most 0": the streak breaks now, the best one stays."""
    avoid = dict(goal_target=0, goal_mode=GoalMode.MAX, start_date=dt.date(2026, 10, 20))
    assert streaks_of([TODAY], **avoid) == (0, 6)


def test_avoid_weekly_limit():
    """At most once a week: twice in the week of the 12th breaks; the week of the 19th is clean."""
    dates = [dt.date(2026, 10, 6), dt.date(2026, 10, 13), dt.date(2026, 10, 16), dt.date(2026, 10, 21)]
    avoid = dict(goal_target=1, goal_period=Period.WEEKLY, goal_mode=GoalMode.MAX)
    assert streaks_of(dates, **avoid) == (1, 2)


# Start date

def test_nothing_before_start_date():
    """A habit starting tomorrow has no streak yet."""
    assert streaks_of([], goal_target=0, goal_mode=GoalMode.MAX, start_date=dt.date(2026, 10, 27)) == (0, 0)


# Random outcomes and sessions

@given(outcomes=st.lists(st.sampled_from(Outcome), max_size=60))
def test_streaks_match_a_plain_count(outcomes):
    """Split at every missed period: best = most met in a stretch, current = met in the last stretch."""
    stretches = [[]]
    for outcome in outcomes:
        if outcome == Outcome.MISSED:
            stretches.append([])
        else:
            stretches[-1].append(outcome)
    met_per_stretch = [stretch.count(Outcome.MET) for stretch in stretches]

    assert streaks(outcomes) == (met_per_stretch[-1], max(met_per_stretch))


@given(dates=SESSION_DAYS, extra=st.dates(min_value=dt.date(2026, 10, 1), max_value=dt.date(2026, 10, 26)),
       period=st.sampled_from([Period.DAILY, Period.WEEKLY]), target=st.integers(1, 3))
def test_one_more_session_never_lowers_a_streak(dates, extra, period, target):
    """At least n: an extra session can only keep or raise the current and best streak."""
    before = streaks_of(dates, goal_period=period, goal_target=target)
    after = streaks_of([*dates, extra], goal_period=period, goal_target=target)

    assert after[0] >= before[0] and after[1] >= before[1]


@given(dates=SESSION_DAYS, extra=st.dates(min_value=dt.date(2026, 10, 1), max_value=dt.date(2026, 10, 26)),
       period=st.sampled_from([Period.DAILY, Period.WEEKLY]), target=st.integers(0, 2))
def test_one_more_slip_never_raises_a_streak(dates, extra, period, target):
    """At most n (avoid): an extra session can only keep or lower the current and best streak."""
    goal = dict(goal_period=period, goal_target=target, goal_mode=GoalMode.MAX)
    before = streaks_of(dates, **goal)
    after = streaks_of([*dates, extra], **goal)

    assert after[0] <= before[0] and after[1] <= before[1]
