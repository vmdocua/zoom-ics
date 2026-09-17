# zoom-ics — tasks

## Done

- [x] Project scaffold: `pyproject.toml` (src layout, `zoom-ics` console script), `.gitignore`
      already excludes `temp/` (real personal schedule data).
- [x] DTOs for both sheets (`models.py`): `ScheduleEntry` and a deliberately minimal `ZoomEntry`
      (`teacher` + raw `description` — no parsing, see [context.md](context.md) "no Zoom text
      parsing").
- [x] Excel reader for `Schedule` + `Zoom` sheets (`excel_reader.py`).
- [x] `current-day` (default), `next-day`, `current-week`, and `next-week` period resolution
      (`period.py`).
- [x] `.ics` builder with inclusion filtering, deterministic UIDs, local-timezone events
      (`ics_builder.py`).
- [x] `click`-based CLI + standalone shebang script `zoom-ics` (`cli.py`), with a default
      `--output` filename (`Zoom_Schedule_<calendars>_<Day|Week>_<date>.ics`, anchored on the
      earliest *resolved* period date) when none is given. Every option has a short flag
      (`-i`/`-o`/`-p`/`-d`/`-I`).
- [x] `--include`/`-I` option (`zoom` [default] / `active` / `all`) controlling which rows become
      events, via `is_included()` in `ics_builder.py`.
- [x] pytest suite with a synthetic workbook fixture (`tests/`), covering the reader, period
      resolution, builder filtering/UID stability, and the CLI end-to-end.
- [x] GitHub Actions CI workflow (lint/test on push + PR, `.github/workflows/ci.yml`).
- [x] `.ai/context.md`, `.ai/spec.md`, this file.
- [x] Anonymized reference workbook `tests/data/Schedule_DB_1.xlsx`, linked from the README, so
      no real personal schedule data needs to live in the repo (or locally under `temp/`) for
      people to see a worked example. Exercised as a smoke test in
      `tests/test_reference_workbook.py` (loads correctly, no real data leaked back in, CLI
      end-to-end for `current-week`).

## Backlog (not started)

- [ ] Additional periods beyond `current-day`/`next-day`/`current-week`/`next-week`: `month`,
      custom date range.
- [ ] `--calendar NAME` filter (currently all calendars in the sheet are always included).
- [ ] Decide whether/what UI to build on top of the CLI (mentioned as a "maybe", not committed).
- [ ] Consider validating and reporting *why* a row was skipped (currently silent) if that turns
      out to be needed for troubleshooting a real schedule.
