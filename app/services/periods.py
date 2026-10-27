"""
Natural calendar periods and the user's today:
    - A period is identified by its first day
    - Weeks are ISO weeks, Monday to Sunday
"""

# Imports
import datetime as dt
from zoneinfo import ZoneInfo

from app.enums import Period

# Months per period (daily and weekly go by days)
MONTHS = {
    Period.MONTHLY:     1,
    Period.QUARTERLY:   3,
    Period.HALFYEARLY:  6,
    Period.YEARLY:      12,
}


def period_start(day: dt.date, period: Period) -> dt.date:
    """First day of the period that contains a day."""
    if period == Period.DAILY:
        return day
    if period == Period.WEEKLY:
        return day - dt.timedelta(days=day.weekday())

    months = MONTHS[period]
    first_month = (day.month - 1) // months * months + 1
    return dt.date(day.year, first_month, 1)


def next_period_start(start: dt.date, period: Period) -> dt.date:
    """First day of the period after the one that starts on a given day."""
    if period == Period.DAILY:
        return start + dt.timedelta(days=1)
    if period == Period.WEEKLY:
        return start + dt.timedelta(days=7)

    years, month_index = divmod(start.month - 1 + MONTHS[period], 12)
    return dt.date(start.year + years, month_index + 1, 1)


def period_end(day: dt.date, period: Period) -> dt.date:
    """Last day of the period that contains a day."""
    return next_period_start(period_start(day, period), period) - dt.timedelta(days=1)


def period_starts(first_day: dt.date, last_day: dt.date, period: Period) -> list[dt.date]:
    """First day of every period, from the one containing first_day to the one containing last_day."""
    starts = []
    start, last = period_start(first_day, period), period_start(last_day, period)

    while start <= last:
        starts.append(start)
        start = next_period_start(start, period)

    return starts


def local_today(timezone: str) -> dt.date:
    """Today in the user's timezone: the server runs in UTC."""
    return dt.datetime.now(ZoneInfo(timezone)).date()
