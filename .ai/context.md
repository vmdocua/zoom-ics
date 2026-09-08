# zoom-ics — AI assistant context

## What this is

A Python CLI (`zoom-ics`, importable as `docsultant.zoom_ics` under `src/`) that reads a
two-sheet `.xlsx` schedule and emits an RFC 5545 `.ics` calendar, one VEVENT per eligible lesson,
with the teacher's raw pasted Zoom invite text folded into `DESCRIPTION`.

See [spec.md](spec.md) for the full functional spec and [tasks.md](tasks.md) for current status.

## Module layout (`src/docsultant/zoom_ics/`)

The package lives under the `docsultant` namespace (`src/docsultant/__init__.py` is a plain
package, not a PEP 420 namespace package) so other Docsultant tools can share the same top-level
namespace later. Import everything as `docsultant.zoom_ics.<module>`.

- `models.py` — `ScheduleEntry` and `ZoomEntry` dataclasses (the DTOs for the two sheets), plus
  `WEEKDAYS`. `ZoomEntry` is intentionally just `teacher` + raw `description` text — it is never
  parsed for a URL/meeting ID/passcode; the whole description is treated as an opaque blob and
  passed through into the event body as-is.
- `excel_reader.py` — reads the `Schedule` and `Zoom` sheets via openpyxl into the DTOs above.
  Rows are recognised as schedule rows purely by whether `Day` is a known weekday abbreviation —
  this is what lets a legend/notes block sit at the bottom of the sheet without special-casing it.
- `period.py` — resolves a named period (`current-day` [default] or `current-week` so far) + a
  reference date into a `{weekday_abbr: date}` mapping. `current-day` maps only the reference
  date's own weekday to itself (a single-entry dict), so only that day's rows are considered.
  This is the extension point for `next-week`/`month`/custom ranges later — add a branch here and
  a matching `click.Choice` value in `cli.py`.
- `ics_builder.py` — filters entries via `has_zoom_room()` (active + teacher assigned + teacher
  has a row in the Zoom sheet) and builds the `icalendar.Calendar`. There's no `LOCATION` field —
  the teacher's raw Zoom description goes straight into `DESCRIPTION`. Event UIDs are
  deterministic (`uuid5` over calendar+date+lesson+start time) so re-running the tool for the
  same week produces the same UIDs — re-importing into Google Calendar updates existing events
  instead of duplicating them.
- `cli.py` — the `click` command (`zoom-ics` console script / `python -m docsultant.zoom_ics`).
  When `--output` isn't given, `_default_output_path()` builds
  `Zoom_Schedule_<calendars>_<Day|Week>_<date>.ics`, where `<calendars>` is computed by
  re-applying the *same* period + `has_zoom_room()` eligibility filtering used by
  `build_calendar()` — deliberately not the same (unfiltered, whole-workbook) set of calendars
  used for `X-WR-CALNAME` in `ics_builder.py`. If you change one filter, check whether the other
  needs to change too.

`zoom-ics` at the repo root is a shebang (`#!/usr/bin/env python3`) wrapper script that adds
`src/` to `sys.path` and calls the same CLI, for running without a `pip install`. It has no `.py`
extension since it's meant to be invoked directly (`./zoom-ics ...`), not imported.

## Key decisions (ask before changing)

- **Namespace**: the package is `docsultant.zoom_ics`, not a top-level `zoom_ics` — the user
  wants Docsultant's internal tools grouped under one `docsultant` namespace. `src/docsultant/`
  has a real `__init__.py` (not an implicit namespace package); the distribution name on PyPI/in
  `pyproject.toml` stays `zoom-ics`.
- **Timezone**: events use the local machine's timezone (`tzlocal.get_localzone()`), not a
  hardcoded one. Chosen explicitly by the user over a fixed `Europe/Kyiv` default.
- **Calendar column**: no `--calendar` filter in v1. All rows are included regardless of their
  `Calendar` value; each event carries its calendar in `CATEGORIES`, and `X-WR-CALNAME` is the
  comma-joined set of distinct calendar names found. A per-calendar filter may be added later.
- **CI scope**: the GitHub Actions workflow (`.github/workflows/ci.yml`) is CI-only (lint/test on
  push+PR). It does not generate or publish `.ics` files on a schedule.
- **No Zoom text parsing**: `ZoomEntry.description` is stored and passed through verbatim, never
  parsed into a URL/meeting ID/passcode. This was tried once (a `zoom_parser.py` module with
  locale-agnostic stem matching for EN/UA/RU invite text) and explicitly reverted — the user
  found it overkill for what's needed. Don't reintroduce parsing without asking.
- **No real personal data in the repo, ever**: `temp/` is gitignored and reserved for a real
  schedule dropped in locally for manual testing — never commit anything from it, and don't leave
  real files sitting there either (an earlier real workbook + a `.ics` generated from it were
  removed from `temp/` once the anonymized reference below existed; if you drop a real file in
  `temp/` again for local testing, clean it up when done rather than leaving it). Never copy real
  teacher names, calendar names, or Zoom links/IDs/passcodes into tests/fixtures/docs — use
  obviously-fake placeholders (e.g. the `zoom.example` domain). Tests run against the synthetic
  workbook built in `tests/conftest.py`, not any real file.
- **Reference workbook**: `tests/data/Schedule_DB_1.xlsx` is committed and mirrors the shape and
  lesson content of a real schedule, but with `Teacher A`/`B`/`C`/`D` in place of real teacher
  names, `Vasya` instead of a real `Calendar` value, and fake `zoom.example` credentials in place
  of real Zoom links/IDs/passcodes. It's for human reference (linked from the README) and isn't
  wired into `pytest` — the pytest fixtures in `tests/conftest.py` are the ones tests actually run
  against. Keep it real-looking but never put real personal data in it.

## Not yet built

- Periods other than `current-day`/`current-week` (next-week, month, custom range).
- Any UI beyond the CLI (mentioned as a "maybe" by the user, not committed to).
- A `--calendar` row filter.
