from datetime import date, time
from zoneinfo import ZoneInfo

import pytest

from docsultant.zoom_ics.ics_builder import build_calendar, has_zoom_room, is_included
from docsultant.zoom_ics.models import ScheduleEntry, ZoomEntry

TZ = ZoneInfo("UTC")

ZOOM_DIRECTORY = {
    "Alice": ZoomEntry(teacher="Alice", description="Join Zoom Meeting\nhttps://zoom.example/j/alice"),
}


def _entry(**overrides) -> ScheduleEntry:
    defaults = dict(
        day="Mon",
        lesson="Math",
        type="gov",
        active="Y",
        start_time=time(8, 30),
        end_time=time(9, 15),
        teacher="Alice",
        calendar="Vasya",
    )
    defaults.update(overrides)
    return ScheduleEntry(**defaults)


def test_has_zoom_room_true_when_active_taught_and_has_link():
    assert has_zoom_room(_entry(), ZOOM_DIRECTORY) is True


def test_has_zoom_room_false_when_inactive():
    assert has_zoom_room(_entry(active="N"), ZOOM_DIRECTORY) is False


def test_has_zoom_room_false_when_teacher_not_assigned():
    assert has_zoom_room(_entry(teacher="n/a"), ZOOM_DIRECTORY) is False


def test_has_zoom_room_false_when_teacher_missing_from_directory():
    assert has_zoom_room(_entry(teacher="Unknown"), ZOOM_DIRECTORY) is False


def test_build_calendar_includes_only_eligible_events():
    entries = [
        _entry(lesson="Math"),
        _entry(lesson="Art", active="N"),
        _entry(lesson="History", teacher="n/a"),
        _entry(lesson="Music", teacher="Unknown"),
    ]
    dates_by_weekday = {"Mon": date(2026, 9, 7)}

    calendar = build_calendar(entries, dates_by_weekday, ZOOM_DIRECTORY, TZ)
    events = list(calendar.walk("VEVENT"))

    assert len(events) == 1
    assert str(events[0]["summary"]) == "Math"
    assert "https://zoom.example/j/alice" in str(events[0]["description"])


def test_build_calendar_uid_is_stable_across_runs():
    entries = [_entry()]
    dates_by_weekday = {"Mon": date(2026, 9, 7)}

    first = list(build_calendar(entries, dates_by_weekday, ZOOM_DIRECTORY, TZ).walk("VEVENT"))
    second = list(build_calendar(entries, dates_by_weekday, ZOOM_DIRECTORY, TZ).walk("VEVENT"))

    assert str(first[0]["uid"]) == str(second[0]["uid"])


def test_build_calendar_sets_calendar_name():
    entries = [_entry(calendar="Vasya")]
    dates_by_weekday = {"Mon": date(2026, 9, 7)}

    calendar = build_calendar(entries, dates_by_weekday, ZOOM_DIRECTORY, TZ)

    assert str(calendar["x-wr-calname"]) == "Vasya"


@pytest.mark.parametrize(
    "entry_overrides, expected",
    [
        ({}, True),
        ({"active": "N"}, False),
        ({"teacher": "n/a"}, False),
        ({"teacher": "Unknown"}, False),
    ],
)
def test_is_included_zoom_mode_matches_has_zoom_room(entry_overrides, expected):
    entry = _entry(**entry_overrides)
    assert is_included(entry, ZOOM_DIRECTORY, "zoom") is has_zoom_room(entry, ZOOM_DIRECTORY)
    assert is_included(entry, ZOOM_DIRECTORY, "zoom") is expected


@pytest.mark.parametrize(
    "entry_overrides, expected",
    [
        ({}, True),
        ({"active": "N"}, False),
        ({"teacher": "n/a"}, True),
        ({"teacher": "Unknown"}, True),
    ],
)
def test_is_included_active_mode_ignores_teacher(entry_overrides, expected):
    assert is_included(_entry(**entry_overrides), ZOOM_DIRECTORY, "active") is expected


@pytest.mark.parametrize(
    "entry_overrides",
    [{}, {"active": "N"}, {"teacher": "n/a"}, {"teacher": "Unknown"}],
)
def test_is_included_all_mode_always_true(entry_overrides):
    assert is_included(_entry(**entry_overrides), ZOOM_DIRECTORY, "all") is True


def test_is_included_unsupported_mode_raises():
    with pytest.raises(ValueError):
        is_included(_entry(), ZOOM_DIRECTORY, "bogus")


def test_build_calendar_active_mode_includes_inactive_teacher_and_no_zoom_room():
    entries = [
        _entry(lesson="Math"),
        _entry(lesson="Art", active="N"),
        _entry(lesson="History", teacher="n/a"),
        _entry(lesson="Music", teacher="Unknown"),
    ]
    dates_by_weekday = {"Mon": date(2026, 9, 7)}

    calendar = build_calendar(entries, dates_by_weekday, ZOOM_DIRECTORY, TZ, include_mode="active")
    summaries = {str(event["summary"]) for event in calendar.walk("VEVENT")}

    assert summaries == {"Math", "History", "Music"}


def test_build_calendar_all_mode_includes_every_row_for_the_period():
    entries = [
        _entry(lesson="Math"),
        _entry(lesson="Art", active="N"),
        _entry(lesson="History", teacher="n/a"),
        _entry(lesson="Music", teacher="Unknown"),
    ]
    dates_by_weekday = {"Mon": date(2026, 9, 7)}

    calendar = build_calendar(entries, dates_by_weekday, ZOOM_DIRECTORY, TZ, include_mode="all")
    summaries = {str(event["summary"]) for event in calendar.walk("VEVENT")}

    assert summaries == {"Math", "Art", "History", "Music"}


def test_build_calendar_event_description_omits_zoom_details_without_a_zoom_entry():
    entries = [_entry(lesson="History", teacher="n/a")]
    dates_by_weekday = {"Mon": date(2026, 9, 7)}

    calendar = build_calendar(entries, dates_by_weekday, ZOOM_DIRECTORY, TZ, include_mode="all")
    events = list(calendar.walk("VEVENT"))

    assert "https://zoom.example" not in str(events[0]["description"])
