"""Resolve a named period (e.g. "current-day") to concrete calendar dates.

"current-day", "next-day", "current-week" and "next-week" are implemented so
far. The function is the single extension point for future periods (month,
a custom range): add a branch here, a label in ``PERIOD_LABELS``, and a
matching ``click.Choice`` value in the CLI.
"""

from __future__ import annotations

from datetime import date, timedelta

from docsultant.zoom_ics.models import WEEKDAYS

DEFAULT_PERIOD = "current-day"
SUPPORTED_PERIODS: tuple[str, ...] = ("current-day", "next-day", "current-week", "next-week")

#: Short, filename-friendly label per period, e.g. for the default output filename.
PERIOD_LABELS: dict[str, str] = {
    "current-day": "Day",
    "next-day": "Day",
    "current-week": "Week",
    "next-week": "Week",
}


def _week_start(reference_date: date) -> date:
    """Return the Monday of the ISO week containing ``reference_date``."""
    return reference_date - timedelta(days=reference_date.weekday())


def _single_day(day: date) -> dict[str, date]:
    return {WEEKDAYS[day.weekday()]: day}


def _week_starting(monday: date) -> dict[str, date]:
    return {weekday: monday + timedelta(days=index) for index, weekday in enumerate(WEEKDAYS)}


def resolve_period(period: str, reference_date: date) -> dict[str, date]:
    """Return a mapping of weekday abbreviation -> concrete date for ``period``.

    :raises ValueError: if ``period`` isn't a supported value.
    """
    if period == "current-day":
        return _single_day(reference_date)

    if period == "next-day":
        return _single_day(reference_date + timedelta(days=1))

    if period == "current-week":
        return _week_starting(_week_start(reference_date))

    if period == "next-week":
        return _week_starting(_week_start(reference_date) + timedelta(days=7))

    raise ValueError(f"Unsupported period {period!r}; supported: {SUPPORTED_PERIODS}")
