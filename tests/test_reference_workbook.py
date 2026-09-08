"""Exercises the tool against the committed, anonymized reference workbook
(tests/data/Schedule_DB_1.xlsx), as a smoke test on a real-shaped, multi-day
file with real Cyrillic lesson names -- complementary to the minimal
synthetic fixture in conftest.py.
"""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from docsultant.zoom_ics.cli import main
from docsultant.zoom_ics.excel_reader import load_workbook_data

REFERENCE_WORKBOOK = Path(__file__).parent / "data" / "Schedule_DB_1.xlsx"

# The only calendar/teacher names this anonymized workbook is allowed to contain. Deliberately
# not a denylist of real names: those must never be typed into a committed file (this one
# included), so any name outside this allowlist -- real or otherwise -- fails the test instead.
EXPECTED_CALENDARS = {"Vasya"}
EXPECTED_TEACHERS = {"Teacher A", "Teacher B", "Teacher C", "Teacher D"}


def test_reference_workbook_loads_and_has_no_real_data():
    entries, zoom_directory = load_workbook_data(REFERENCE_WORKBOOK)

    # 8 lessons/day, Mon-Fri; legend/blank rows at the bottom are excluded.
    assert len(entries) == 40
    assert {entry.day for entry in entries} == {"Mon", "Tue", "Wed", "Thu", "Fri"}
    assert {entry.calendar for entry in entries} == EXPECTED_CALENDARS
    assert set(zoom_directory) == EXPECTED_TEACHERS
    assert {entry.teacher for entry in entries} <= EXPECTED_TEACHERS | {"n/a"}

    for zoom_entry in zoom_directory.values():
        assert "zoom.example" in zoom_entry.description
        assert "zoom.us" not in zoom_entry.description


def test_reference_workbook_current_week_via_cli(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        main,
        ["--input", str(REFERENCE_WORKBOOK), "--period", "current-week", "--date", "2026-09-08"],
    )

    assert result.exit_code == 0, result.output
    expected = tmp_path / "Zoom_Schedule_Vasya_Week_2026-09-08.ics"
    assert expected.exists()
    assert f"Wrote 14 event(s) to {expected.name}" in result.output

    content = expected.read_text()
    assert "BEGIN:VCALENDAR" in content
    assert "SUMMARY:Математика" in content
    # "Малювання" has no assigned teacher (n/a) and must be excluded.
    assert "SUMMARY:Малювання" not in content
