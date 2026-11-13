"""
Natural calendar periods and the user's today:
    - Weeks from Monday to Sunday (v1 bug 2)
    - Every period kind, across year ends and leap years
    - Random days: every period holds its day, and periods follow one another without gaps
"""

# Imports
import datetime as dt
import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.enums import Period
from app.services.periods import local_today, next_period_start, period_end, period_start, period_starts

# Random days and periods
DAYS = st.dates(min_value=dt.date(2000, 1, 1), max_value=dt.date(2100, 12, 31))
PERIODS = st.sampled_from(Period)


def test_week_runs_monday_to_sunday():
    """v1 bug 2: Thursday 15/10/2026 gave 9/10 to 11/10, the tail of the week before."""
    thursday = dt.date(2026, 10, 15)

    assert period_start(thursday, Period.WEEKLY) == dt.date(2026, 10, 12)
    assert period_end(thursday, Period.WEEKLY) == dt.date(2026, 10, 18)


@pytest.mark.parametrize(("day", "period", "start", "end"), [
    (dt.date(2026, 3, 15),  Period.DAILY,       dt.date(2026, 3, 15),   dt.date(2026, 3, 15)),
    (dt.date(2026, 1, 1),   Period.WEEKLY,      dt.date(2025, 12, 29),  dt.date(2026, 1, 4)),       # ISO week across years
    (dt.date(2028, 2, 10),  Period.MONTHLY,     dt.date(2028, 2, 1),    dt.date(2028, 2, 29)),      # Leap year
    (dt.date(2026, 11, 5),  Period.QUARTERLY,   dt.date(2026, 10, 1),   dt.date(2026, 12, 31)),
    (dt.date(2026, 6, 30),  Period.HALFYEARLY,  dt.date(2026, 1, 1),    dt.date(2026, 6, 30)),
    (dt.date(2026, 7, 1),   Period.HALFYEARLY,  dt.date(2026, 7, 1),    dt.date(2026, 12, 31)),
    (dt.date(2026, 3, 15),  Period.YEARLY,      dt.date(2026, 1, 1),    dt.date(2026, 12, 31)),
])
def test_period_bounds(day, period, start, end):
    """First and last day of the period that contains a day."""
    assert period_start(day, period) == start
    assert period_end(day, period) == end


def test_period_starts_cover_every_period():
    """From the period of the first day to the period of the last one, both included."""
    starts = period_starts(dt.date(2026, 11, 20), dt.date(2027, 2, 3), Period.MONTHLY)

    assert starts == [dt.date(2026, 11, 1), dt.date(2026, 12, 1), dt.date(2027, 1, 1), dt.date(2027, 2, 1)]


@pytest.mark.parametrize(("utc_moment", "madrid_day"), [
    (dt.datetime(2026, 10, 26, 23, 30, tzinfo=dt.UTC), dt.date(2026, 10, 27)),     # Winter: Madrid is UTC+1
    (dt.datetime(2026, 7, 10, 22, 30, tzinfo=dt.UTC),  dt.date(2026, 7, 11)),      # Summer: Madrid is UTC+2
    (dt.datetime(2026, 7, 10, 21, 30, tzinfo=dt.UTC),  dt.date(2026, 7, 10)),
])
def test_today_turns_at_local_midnight(utc_moment, madrid_day):
    """At 00:30 in Madrid it is already the next day, although the server (UTC) is still on the previous one."""
    assert local_today("Europe/Madrid", now=utc_moment) == madrid_day


def test_local_today_follows_timezone():
    """UTC+14 and UTC-11 are always on different days: the timezone is applied (and tzdata works on Windows)."""
    ahead = local_today("Pacific/Kiritimati")
    behind = local_today("Pacific/Pago_Pago")

    assert (ahead - behind).days in (1, 2)


# Random days

@given(day=DAYS, period=PERIODS)
def test_period_holds_its_day(day, period):
    """Start ≤ day ≤ end, the start is its own period's start, and the next period begins the day after the end."""
    start, end = period_start(day, period), period_end(day, period)

    assert start <= day <= end
    assert period_start(start, period) == period_start(end, period) == start
    assert next_period_start(start, period) == end + dt.timedelta(days=1)


@given(first=DAYS, last=DAYS, period=PERIODS)
def test_period_starts_without_gaps(first, last, period):
    """From first's period to last's, each start right after the one before; nothing when last comes first."""
    starts = period_starts(first, last, period)

    if period_start(last, period) < period_start(first, period):
        assert starts == []
        return

    assert starts[0] == period_start(first, period)
    assert starts[-1] == period_start(last, period)
    assert all(next_period_start(a, period) == b for a, b in zip(starts, starts[1:], strict=False))
