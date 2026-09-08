from pathlib import Path

from click.testing import CliRunner

from docsultant.zoom_ics.cli import main


def test_cli_generates_ics_for_current_week(sample_workbook_path: Path, tmp_path: Path):
    output_path = tmp_path / "out.ics"
    runner = CliRunner()

    result = runner.invoke(
        main,
        [
            "--input",
            str(sample_workbook_path),
            "--output",
            str(output_path),
            "--period",
            "current-week",
            "--date",
            "2026-09-08",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Wrote" in result.output
    assert output_path.exists()

    content = output_path.read_text()
    assert "BEGIN:VCALENDAR" in content
    assert "SUMMARY:Math" in content
    assert "SUMMARY:English" in content
    # Excluded rows must not appear.
    assert "SUMMARY:Art" not in content
    assert "SUMMARY:History" not in content
    assert "SUMMARY:Music" not in content


def test_cli_defaults_to_current_day(sample_workbook_path: Path, tmp_path: Path):
    output_path = tmp_path / "out.ics"
    runner = CliRunner()

    # 2026-09-07 is a Monday: only "Math" (Mon, eligible) should appear;
    # "English" is on Wednesday and must be excluded by the current-day default.
    result = runner.invoke(
        main,
        [
            "--input",
            str(sample_workbook_path),
            "--output",
            str(output_path),
            "--date",
            "2026-09-07",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Wrote 1 event(s)" in result.output

    content = output_path.read_text()
    assert "SUMMARY:Math" in content
    assert "SUMMARY:English" not in content


def test_cli_default_output_filename_for_current_day(
    sample_workbook_path: Path, tmp_path: Path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    # 2026-09-07 is a Monday: only "Vasya" (via "Math") is in scope.
    result = runner.invoke(main, ["--input", str(sample_workbook_path), "--date", "2026-09-07"])

    assert result.exit_code == 0, result.output
    expected = tmp_path / "Zoom_Schedule_Vasya_Day_2026-09-07.ics"
    assert expected.exists()
    assert f"Wrote 1 event(s) to {expected.name}" in result.output


def test_cli_default_output_filename_for_current_week(
    sample_workbook_path: Path, tmp_path: Path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    # The week of 2026-09-08 includes both "Vasya" (Math) and "Other" (English) calendars.
    result = runner.invoke(
        main,
        ["--input", str(sample_workbook_path), "--period", "current-week", "--date", "2026-09-08"],
    )

    assert result.exit_code == 0, result.output
    expected = tmp_path / "Zoom_Schedule_Other-Vasya_Week_2026-09-08.ics"
    assert expected.exists()
    assert f"Wrote 2 event(s) to {expected.name}" in result.output


def test_cli_include_active_short_flag(sample_workbook_path: Path, tmp_path: Path):
    output_path = tmp_path / "out.ics"
    runner = CliRunner()

    # -I active: Active=Y rows regardless of teacher/Zoom room, so "History" (inactive) is
    # still excluded but "Art" (n/a teacher) and "Music" (no Zoom room) are now included.
    result = runner.invoke(
        main,
        [
            "--input",
            str(sample_workbook_path),
            "--output",
            str(output_path),
            "--period",
            "current-week",
            "--date",
            "2026-09-08",
            "-I",
            "active",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Wrote 4 event(s)" in result.output

    content = output_path.read_text()
    for summary in ("Math", "Art", "Music", "English"):
        assert f"SUMMARY:{summary}" in content
    assert "SUMMARY:History" not in content


def test_cli_include_all(sample_workbook_path: Path, tmp_path: Path):
    output_path = tmp_path / "out.ics"
    runner = CliRunner()

    # --include all: every row for the period, including the inactive "History" row.
    result = runner.invoke(
        main,
        [
            "--input",
            str(sample_workbook_path),
            "--output",
            str(output_path),
            "--period",
            "current-week",
            "--date",
            "2026-09-08",
            "--include",
            "all",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Wrote 5 event(s)" in result.output

    content = output_path.read_text()
    for summary in ("Math", "Art", "History", "Music", "English"):
        assert f"SUMMARY:{summary}" in content


def test_cli_requires_existing_input_file(tmp_path: Path):
    runner = CliRunner()

    result = runner.invoke(main, ["--input", str(tmp_path / "missing.xlsx")])

    assert result.exit_code != 0
