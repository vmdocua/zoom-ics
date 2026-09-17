"""Command-line interface for zoom-ics."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

import click
import tzlocal

from docsultant.zoom_ics.excel_reader import load_workbook_data
from docsultant.zoom_ics.ics_builder import (
    DEFAULT_INCLUDE_MODE,
    SUPPORTED_INCLUDE_MODES,
    build_calendar,
    is_included,
)
from docsultant.zoom_ics.models import ScheduleEntry, ZoomEntry
from docsultant.zoom_ics.period import DEFAULT_PERIOD, PERIOD_LABELS, SUPPORTED_PERIODS, resolve_period

_FILENAME_UNSAFE_RE = re.compile(r"[^A-Za-z0-9_-]+")


def _sanitize_for_filename(text: str) -> str:
    return _FILENAME_UNSAFE_RE.sub("_", text).strip("_")


def _default_output_path(
    entries: list[ScheduleEntry],
    dates_by_weekday: dict[str, date],
    zoom_directory: dict[str, ZoomEntry],
    period: str,
    include_mode: str,
) -> Path:
    """Build "Zoom_Schedule_<calendars>_<Day|Week>_<date>.ics", e.g.

    ``Zoom_Schedule_Vasya_Day_2026-09-18.ics`` or, with two calendars,
    ``Zoom_Schedule_Other-Vasya_Week_2026-09-18.ics``. The calendar names are
    those of the events actually included in this run (same period +
    ``include_mode`` filtering as :func:`build_calendar`), not every calendar
    mentioned anywhere in the workbook. The date is the earliest date in the
    *resolved* period (e.g. the Monday of the target week for
    "current-week"/"next-week"), not the raw ``--date`` value -- for
    "next-day"/"next-week" those differ.
    """
    calendar_names = sorted(
        {
            entry.calendar
            for entry in entries
            if entry.calendar
            and entry.day in dates_by_weekday
            and is_included(entry, zoom_directory, include_mode)
        }
    )
    calendars_slug = "-".join(_sanitize_for_filename(name) for name in calendar_names) or "Schedule"
    period_label = PERIOD_LABELS[period]
    anchor_date = min(dates_by_weekday.values())
    return Path(f"Zoom_Schedule_{calendars_slug}_{period_label}_{anchor_date.isoformat()}.ics")


@click.command()
@click.option(
    "--input",
    "-i",
    "input_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to the source .xlsx schedule file.",
)
@click.option(
    "--output",
    "-o",
    "output_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help=(
        "Path to write the generated .ics file. Defaults to "
        "Zoom_Schedule_<calendars>_<Day|Week>_<date>.ics."
    ),
)
@click.option(
    "--period",
    "-p",
    type=click.Choice(SUPPORTED_PERIODS),
    default=DEFAULT_PERIOD,
    show_default=True,
    help="Which period to generate events for.",
)
@click.option(
    "--date",
    "-d",
    "reference_date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="Reference date used to resolve the period (defaults to today, local time).",
)
@click.option(
    "--include",
    "-I",
    "include_mode",
    type=click.Choice(SUPPORTED_INCLUDE_MODES),
    default=DEFAULT_INCLUDE_MODE,
    show_default=True,
    help=(
        "Which rows to include: 'zoom' (Active=Y, has a teacher, and that teacher has a Zoom "
        "room), 'active' (Active=Y, regardless of teacher/Zoom room), or 'all' (every row for "
        "the period, regardless of Active/Teacher)."
    ),
)
def main(
    input_path: Path,
    output_path: Path | None,
    period: str,
    reference_date: datetime | None,
    include_mode: str,
) -> None:
    """Convert an .xlsx schedule + Zoom directory into a .ics calendar."""
    ref_date: date = reference_date.date() if reference_date else date.today()
    tz = tzlocal.get_localzone()

    entries, zoom_directory = load_workbook_data(input_path)
    dates_by_weekday = resolve_period(period, ref_date)
    calendar = build_calendar(entries, dates_by_weekday, zoom_directory, tz, include_mode)

    if output_path is None:
        output_path = _default_output_path(entries, dates_by_weekday, zoom_directory, period, include_mode)

    output_path.write_bytes(calendar.to_ical())

    event_count = sum(1 for component in calendar.walk("VEVENT"))
    click.echo(f"Wrote {event_count} event(s) to {output_path}")


if __name__ == "__main__":
    main()
