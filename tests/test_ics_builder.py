from datetime import date, time
from zoneinfo import ZoneInfo

from docsultant.zoom_ics.ics_builder import build_calendar, has_zoom_room
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
