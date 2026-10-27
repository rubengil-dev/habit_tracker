"""
Badge values and tiers:
    - Recalculation of every badge of a habit after a change
    - One value per badge kind, over the sessions its tag filters let through
    - Progress in the current period, for consistency and streak badges
"""

# Imports
import datetime as dt
from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import BadgeKind, TagRule, Tier
from app.models import Badge, Habit
from app.services.history import EntryFacts, load_history
from app.services.periods import period_start
from app.services.streaks import Outcome, period_outcomes, streaks
from app.services.tiers import tier_for


@dataclass
class BadgeChange:
    """A badge whose value or tier has just changed, with its previous state for the animation."""

    badge: Badge
    old_value: float | None
    old_tier: Tier


@dataclass
class Progress:
    """Where a consistency or streak badge stands today."""

    period_count: int                   # Sessions that count in the current period
    target: int
    current_streak: int | None          # Streak badges only


def recalculate_badges(db: Session, habit: Habit, today: dt.date,
                       history: list[EntryFacts] | None = None) -> list[BadgeChange]:
    """
    Badges of a habit recalculated after a change, or on reading them (avoid badges grow with time):
        - New value and tier saved in each badge; the caller commits
        - Only the badges that changed are reported
        - history: the habit's sessions, if already loaded
    """
    history = load_history(db, habit.id) if history is None else history
    changes = []

    for badge in db.scalars(select(Badge).where(Badge.habit_id == habit.id)):
        old_value, old_tier = badge.current_value, badge.current_tier
        badge.current_value = badge_value(badge, history, habit.start_date, today)
        badge.current_tier = tier_for(badge, badge.current_value)

        if (badge.current_value, badge.current_tier) != (old_value, old_tier):
            changes.append(BadgeChange(badge, old_value, old_tier))

    return changes


def badge_value(badge: Badge, history: list[EntryFacts], start_date: dt.date, today: dt.date) -> float | None:
    """Value of a badge over the sessions that pass its tag filters; None when there is nothing to measure."""
    entries = filter_by_tags(badge, history)

    match badge.kind:
        case BadgeKind.HISTORIC:
            return historic_value(badge, entries)
        case BadgeKind.RECORD:
            return record_value(badge, entries)
        case BadgeKind.OBJECTIVE:
            return float(len(passing(badge, entries)))
        case BadgeKind.CONSISTENCY:
            return float(badge_outcomes(badge, entries, start_date, today).count(Outcome.MET))
        case BadgeKind.STREAK:
            current, best = streaks(badge_outcomes(badge, entries, start_date, today))
            return float(best)


def badge_progress(badge: Badge, history: list[EntryFacts], start_date: dt.date, today: dt.date) -> Progress | None:
    """Current period ("3/7") of consistency and streak badges, plus the current streak of the latter."""
    if badge.kind not in (BadgeKind.CONSISTENCY, BadgeKind.STREAK):
        return None

    tagged = filter_by_tags(badge, history)
    current = period_start(today, badge.period)
    period_count = sum(1 for entry in passing(badge, tagged) if period_start(entry.date, badge.period) == current)

    current_streak = None
    if badge.kind == BadgeKind.STREAK:
        current_streak, best = streaks(badge_outcomes(badge, tagged, start_date, today))

    return Progress(period_count, badge.target, current_streak)


# Session filters

def filter_by_tags(badge: Badge, history: list[EntryFacts]) -> list[EntryFacts]:
    """
    Sessions that count for a badge:
        - With every required tag, and none of the excluded ones
        - Untagged only, if the badge says so
    """
    required = {rule.tag_id for rule in badge.tag_rules if rule.rule == TagRule.REQUIRED}
    excluded = {rule.tag_id for rule in badge.tag_rules if rule.rule == TagRule.EXCLUDED}

    return [
        entry for entry in history
        if required <= entry.tag_ids
        and not excluded & entry.tag_ids
        and not (badge.untagged_only and entry.tag_ids)
    ]


def passing(badge: Badge, entries: list[EntryFacts]) -> list[EntryFacts]:
    """Sessions whose metric passes the badge's bar; all of them if it has no bar."""
    if badge.threshold is None:
        return entries

    passed = []
    for entry in entries:
        value = entry.values.get(badge.metric_id)
        if value is not None and (value >= badge.threshold if badge.higher_is_better else value <= badge.threshold):
            passed.append(entry)

    return passed


# Values per kind

def historic_value(badge: Badge, entries: list[EntryFacts]) -> float | None:
    """Sum of the metric; without a metric, number of sessions."""
    if badge.metric_id is None:
        return float(len(entries))

    values = metric_values(badge, entries)
    return sum(values) if values else None


def record_value(badge: Badge, entries: list[EntryFacts]) -> float | None:
    """Best value of the metric in one session: highest or lowest."""
    values = metric_values(badge, entries)

    if not values:
        return None
    return max(values) if badge.higher_is_better else min(values)


def badge_outcomes(badge: Badge, entries: list[EntryFacts], start_date: dt.date, today: dt.date) -> list[Outcome]:
    """Outcome of every period of a consistency or streak badge, with the sessions that pass its bar."""
    dates = [entry.date for entry in passing(badge, entries)]
    return period_outcomes(dates, badge.period, badge.target, badge.mode, start_date, today)


def metric_values(badge: Badge, entries: list[EntryFacts]) -> list[float]:
    """Values of the badge's metric, in the sessions that have it."""
    return [entry.values[badge.metric_id] for entry in entries if badge.metric_id in entry.values]
