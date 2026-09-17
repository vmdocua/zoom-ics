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
- `period.py` — resolves a named period (`current-day` [default], `next-day`, `current-week`,
  `next-week`) + a reference date into a `{weekday_abbr: date}` mapping. Day periods map only one
  weekday to one date (a single-entry dict); week periods map all 7. This is the extension point
  for `month`/custom ranges later — add a branch here, a label in `PERIOD_LABELS`, and a matching
  `click.Choice` value in `cli.py`.
- `ics_builder.py` — `is_included()` dispatches on `include_mode` (`"zoom"` [default]: active +
  teacher assigned + teacher has a Zoom row, via `has_zoom_room()`; `"active"`: `Active=="Y"`
  only; `"all"`: everything) and `build_calendar()` filters entries through it. `zoom_directory`
  is looked up with `.get()`, not `[...]`, since under `"active"`/`"all"` a row's teacher may have
  no Zoom entry — `build_event()`'s `zoom_entry` parameter is `ZoomEntry | None`, and
  `_event_description()` just omits the Zoom text when it's `None`. There's no `LOCATION` field
  regardless — the teacher's raw Zoom description goes straight into `DESCRIPTION`. Event UIDs
  are deterministic (`uuid5` over calendar+date+lesson+start time) so re-running the tool for the
  same week produces the same UIDs — re-importing into Google Calendar updates existing events
  instead of duplicating them.
- `cli.py` — the `click` command (`zoom-ics` console script / `python -m docsultant.zoom_ics`).
  `--include`/`-I` (`SUPPORTED_INCLUDE_MODES`/`DEFAULT_INCLUDE_MODE` from `ics_builder.py`) is
  threaded into both `build_calendar()` and `_default_output_path()`. When `--output` isn't
  given, `_default_output_path()` builds `Zoom_Schedule_<calendars>_<Day|Week>_<date>.ics`, where
  `<calendars>` is computed by re-applying the *same* period + `is_included()` filtering used by
  `build_calendar()` — deliberately not the same (unfiltered, whole-workbook) set of calendars
  used for `X-WR-CALNAME` in `ics_builder.py`. If you change one filter, check whether the other
  needs to change too. The filename's `<date>` is `min(dates_by_weekday.values())` — the earliest
  *resolved* date, not the raw `--date`/`reference_date` input — which matters once `next-day`/
  `next-week` exist: raw `--date` names a day in the *current* period, not the target one.

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
- **`--include`/`-I` naming**: option is named `--include` (values `zoom`/`active`/`all`), not
  `--mode` — chosen over `--mode` for reading naturally as "which rows to include" without
  needing to explain what it's a mode *of*. Short flag is `-I` (capital), since `-i` was already
  `--input`.
- **Short flags**: every option has one — `-i`/`-o`/`-p`/`-d`/`-I` for
  `--input`/`--output`/`--period`/`--date`/`--include`. Keep this true for any new option: pick a
  letter that doesn't collide (capitalize, as `-I` does, if the natural lowercase is taken).
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
  of real Zoom links/IDs/passcodes. It's for human reference (linked from the README) *and* is
  exercised by `tests/test_reference_workbook.py` as a smoke test on a real-shaped, multi-day,
  Cyrillic-content file — complementary to the minimal synthetic fixture in `tests/conftest.py`
  that the rest of the suite uses. That test checks calendar/teacher names against an *allowlist*
  of the known placeholder values (`EXPECTED_CALENDARS`/`EXPECTED_TEACHERS`) rather than a
  denylist of real names — a denylist would mean typing real personal data into a committed test
  file to guard against it, which defeats the purpose. Keep the workbook real-looking but never
  put real personal data in it (or in any test that reads it).

## Not yet built

- Periods other than `current-day`/`next-day`/`current-week`/`next-week` (e.g. month, custom
  range).
- Any UI beyond the CLI (mentioned as a "maybe" by the user, not committed to).
- A `--calendar` row filter.
