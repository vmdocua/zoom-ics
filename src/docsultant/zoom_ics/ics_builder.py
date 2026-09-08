"""Build an .ics calendar from schedule entries and their Zoom directory entries."""

from __future__ import annotations

import re
import uuid
from datetime import date, datetime, tzinfo

from icalendar import Calendar, Event

from docsultant.zoom_ics.models import ScheduleEntry, ZoomEntry

#: Fixed namespace so the same lesson/date always gets the same UID,
#: letting re-imports update existing events instead of duplicating them.
_UID_NAMESPACE = uuid.UUID("2c6f9a0e-9b7b-4f0a-8f4b-3a2f2a2f5e7d")

_UID_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slug(*parts: str) -> str:
    joined = "-".join(parts).lower()
    return _UID_SLUG_RE.sub("-", joined).strip("-")


def has_zoom_room(entry: ScheduleEntry, zoom_directory: dict[str, ZoomEntry]) -> bool:
    """True if ``entry`` is eligible for inclusion: active, taught, and has a Zoom entry."""
    return entry.is_active and entry.has_teacher and entry.teacher in zoom_directory


def _event_description(entry: ScheduleEntry, zoom_entry: ZoomEntry) -> str:
    return f"Teacher: {entry.teacher}\nCalendar: {entry.calendar}\n\n{zoom_entry.description}"


def build_event(entry: ScheduleEntry, event_date: date, zoom_entry: ZoomEntry, tz: tzinfo) -> Event:
    """Build a single VEVENT for ``entry`` occurring on ``event_date``."""
    dtstart = datetime.combine(event_date, entry.start_time, tzinfo=tz)
    dtend = datetime.combine(event_date, entry.end_time, tzinfo=tz)

    event = Event()
    event.add("summary", entry.lesson)
    event.add("dtstart", dtstart)
    event.add("dtend", dtend)
    event.add("categories", [entry.calendar, entry.type])
    event.add("description", _event_description(entry, zoom_entry))
    event["uid"] = str(
        uuid.uuid5(_UID_NAMESPACE, _slug(entry.calendar, event_date.isoformat(), entry.lesson, str(entry.start_time)))
    ) + "@zoom-ics"
    return event


def build_calendar(
    entries: list[ScheduleEntry],
    dates_by_weekday: dict[str, date],
    zoom_directory: dict[str, ZoomEntry],
    tz: tzinfo,
) -> Calendar:
    """Build the full .ics :class:`~icalendar.Calendar` for the given entries and period."""
    calendar_names = sorted({entry.calendar for entry in entries if entry.calendar})
    cal = Calendar()
    cal.add("prodid", "-//zoom-ics//zoom-ics//EN")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", ", ".join(calendar_names) or "Schedule")

    for entry in entries:
        if not has_zoom_room(entry, zoom_directory):
            continue
        event_date = dates_by_weekday.get(entry.day)
        if event_date is None:
            continue
        zoom_entry = zoom_directory[entry.teacher]
        cal.add_component(build_event(entry, event_date, zoom_entry, tz))

    cal.add_missing_timezones()
    return cal
