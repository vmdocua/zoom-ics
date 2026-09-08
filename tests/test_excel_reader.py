from datetime import time
from pathlib import Path

from docsultant.zoom_ics.excel_reader import load_workbook_data


def test_load_workbook_data_reads_schedule_and_zoom(sample_workbook_path: Path):
    entries, zoom_directory = load_workbook_data(sample_workbook_path)

    # Legend / blank rows are skipped; only real weekday rows remain.
    assert len(entries) == 5

    math_entry = next(e for e in entries if e.lesson == "Math")
    assert math_entry.day == "Mon"
    assert math_entry.type == "gov"
    assert math_entry.is_active is True
    assert math_entry.start_time == time(8, 30)
    assert math_entry.end_time == time(9, 15)
    assert math_entry.teacher == "Alice Teacher"
    assert math_entry.has_teacher is True
    assert math_entry.calendar == "Vasya"

    art_entry = next(e for e in entries if e.lesson == "Art")
    assert art_entry.has_teacher is False

    history_entry = next(e for e in entries if e.lesson == "History")
    assert history_entry.is_active is False

    assert set(zoom_directory) == {"Alice Teacher", "Bob Teacher"}
    assert zoom_directory["Alice Teacher"].teacher == "Alice Teacher"
    assert "zoom.example/j/000000001" in zoom_directory["Alice Teacher"].description
    assert "zoom.example/j/000000002" in zoom_directory["Bob Teacher"].description
