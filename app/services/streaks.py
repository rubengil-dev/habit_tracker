"""
Goals over natural periods ("at least / at most n sessions per period"):
    - Outcome of every period since the habit started
    - Current and best streak
    - Streaks of a habit, from its own goal, and how its current period is going
"""

# Imports
import datetime as dt
from collections import Counter
from enum import Enum

from app.enums import GoalMode, Period
from app.models import Habit
from app.services.history import EntryFacts
from app.services.periods import period_start, period_starts


class Outcome(str, Enum):
    MET = "met"
    MISSED = "missed"
    OPEN = "open"                   # Current period, still undecided


def habit_streaks(habit: Habit, history: list[EntryFacts], today: dt.date) -> tuple[int, int]:
    """Current and best streak of a habit's goal, counting every session → (current, best)."""
    dates = [entry.date for entry in history]
    outcomes = period_outcomes(dates, habit.goal_period, habit.goal_target, habit.goal_mode, habit.start_date, today)
    return streaks(outcomes)


def goal_so_far(habit: Habit, history: list[EntryFacts], today: dt.date) -> tuple[int, bool]:
    """
    Sessions in the goal's current period → (count, met so far):
        - At least n: met once it reaches n
        - At most n (avoid): met while it does not go over n
    """
    current = period_start(today, habit.goal_period)
    count = sum(1 for entry in history if period_start(entry.date, habit.goal_period) == current)

    met = count >= habit.goal_target if habit.goal_mode == GoalMode.MIN else count <= habit.goal_target
    return count, met


def period_outcomes(dates: list[dt.date], period: Period, target: int, mode: GoalMode,
                    start_date: dt.date, today: dt.date) -> list[Outcome]:
    """
    Outcome of every period from the habit's start date to today, oldest first:
        - Closed periods: met or missed
        - Current period, at least n: met as soon as it is met, open until then
        - Current period, at most n (avoid): missed as soon as it goes over, open until it closes
    """
    counts = Counter(period_start(day, period) for day in dates)
    current = period_start(today, period)
    outcomes = []

    for start in period_starts(start_date, today, period):
        met = counts[start] >= target if mode == GoalMode.MIN else counts[start] <= target

        if start < current:
            outcomes.append(Outcome.MET if met else Outcome.MISSED)
        elif mode == GoalMode.MIN:
            outcomes.append(Outcome.MET if met else Outcome.OPEN)
        else:
            outcomes.append(Outcome.OPEN if met else Outcome.MISSED)

    return outcomes


def streaks(outcomes: list[Outcome]) -> tuple[int, int]:
    """
    Consecutive met periods → (current, best):
        - A missed period breaks the streak; an open one neither adds nor breaks
    """
    current = best = 0

    for outcome in outcomes:
        if outcome == Outcome.MET:
            current += 1
            best = max(best, current)
        elif outcome == Outcome.MISSED:
            current = 0

    return current, best
