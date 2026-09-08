from __future__ import annotations

from pathlib import Path

import openpyxl
import pytest

SCHEDULE_ROWS = [
    ("Day", "Lesson", "Type", "Active", "Start Time", "End Time", "Teacher", "Calendar"),
    # Active, has teacher, teacher has a Zoom room -> included.
    ("Mon", "Math", "gov", "Y", "08:30", "09:15", "Alice Teacher", "Vasya"),
    # Active, teacher is n/a -> excluded (no teacher assigned).
    ("Mon", "Art", "gov", "Y", "09:25", "10:10", "n/a", "Vasya"),
    # Not active -> excluded even though teacher has a Zoom room.
    ("Tue", "History", "gov", "N", "08:30", "09:15", "Alice Teacher", "Vasya"),
    # Active, has teacher, but teacher isn't in the Zoom directory -> excluded.
    ("Tue", "Music", "alsko", "Y", "09:25", "10:10", "No Zoom Teacher", "Vasya"),
    # Active, has teacher with a Zoom room -> included, second calendar.
    ("Wed", "English", "alsko", "Y", "13:25", "14:10", "Bob Teacher", "Other"),
    # Legend / stray rows that must be skipped because "Day" isn't a weekday.
    ("Legend:", None, None, None, None, None, None, None),
    ("Type: gov = government-funded lesson.", None, None, None, None, None, None, None),
    (None, None, None, None, None, None, None, None),
]

ZOOM_ROWS = [
    ("Teacher", "Description"),
    (
        "Alice Teacher",
        "Join Zoom Meeting\nhttps://zoom.example/j/000000001\nMeeting ID: 000 000 001\nPasscode: dummy1",
    ),
    (
        "Bob Teacher",
        "Join Zoom Meeting\nhttps://zoom.example/j/000000002\nMeeting ID: 000 000 002\nPasscode: dummy2",
    ),
    # No Zoom room on file for "No Zoom Teacher" on purpose.
]


def _write_workbook(path: Path) -> None:
    workbook = openpyxl.Workbook()
    schedule_sheet = workbook.active
    schedule_sheet.title = "Schedule"
    for row in SCHEDULE_ROWS:
        schedule_sheet.append(row)

    zoom_sheet = workbook.create_sheet("Zoom")
    for row in ZOOM_ROWS:
        zoom_sheet.append(row)

    workbook.save(path)


@pytest.fixture
def sample_workbook_path(tmp_path: Path) -> Path:
    path = tmp_path / "sample_schedule.xlsx"
    _write_workbook(path)
    return path
