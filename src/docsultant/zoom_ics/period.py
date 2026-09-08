"""Resolve a named period (e.g. "current-day") to concrete calendar dates.

Only "current-day" and "current-week" are implemented for now. The function
is the single extension point for future periods (next-week, month, a
custom range): add a branch here and a matching ``click.Choice`` value in
the CLI.
"""

from __future__ import annotations

from datetime import date, timedelta

from docsultant.zoom_ics.models import WEEKDAYS

DEFAULT_PERIOD = "current-day"
SUPPORTED_PERIODS: tuple[str, ...] = ("current-day", "current-week")

#: Short, filename-friendly label per period, e.g. for the default output filename.
PERIOD_LABELS: dict[str, str] = {"current-day": "Day", "current-week": "Week"}


def _week_start(reference_date: date) -> date:
    """Return the Monday of the ISO week containing ``reference_date``."""
    return reference_date - timedelta(days=reference_date.weekday())


def resolve_period(period: str, reference_date: date) -> dict[str, date]:
    """Return a mapping of weekday abbreviation -> concrete date for ``period``.

    :raises ValueError: if ``period`` isn't a supported value.
    """
    if period == "current-day":
        weekday = WEEKDAYS[reference_date.weekday()]
        return {weekday: reference_date}

    if period == "current-week":
        monday = _week_start(reference_date)
        return {weekday: monday + timedelta(days=index) for index, weekday in enumerate(WEEKDAYS)}

    raise ValueError(f"Unsupported period {period!r}; supported: {SUPPORTED_PERIODS}")
