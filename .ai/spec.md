# zoom-ics — functional spec

## Goal

Convert a human-maintained `.xlsx` weekly schedule plus a Zoom directory into an `.ics` calendar
file that can be imported into Google Calendar (or any RFC 5545 consumer), so lessons show up
with the teacher's Zoom invite text attached.

## Input: `Schedule` sheet

| Column       | Meaning                                                                 |
|--------------|--------------------------------------------------------------------------|
| Day          | `Mon`..`Sun`. Any row where this isn't a known weekday is ignored (legend/notes rows). |
| Lesson       | Free-text lesson name. Becomes the event `SUMMARY`.                     |
| Type         | Free-text category (e.g. `gov`, `alsko`). Added to `CATEGORIES`.        |
| Active       | `Y` to include the row, anything else to exclude it.                    |
| Start Time   | `HH:MM`.                                                                  |
| End Time     | `HH:MM`.                                                                  |
| Teacher      | A name present in the `Zoom` sheet, or `n/a` if no live session.        |
| Calendar     | Groups rows (e.g. by student/child). All calendars present are included in one `.ics` in v1 — no CLI filter. |

## Input: `Zoom` sheet

| Column      | Meaning                                                                  |
|-------------|---------------------------------------------------------------------------|
| Teacher     | Matches `Schedule.Teacher`.                                              |
| Description | A pasted Zoom invite block, free text. Stored and used as-is — never parsed into a URL/meeting ID/passcode. |

## Inclusion rule

A `Schedule` row becomes a calendar event if and only if:

1. `Active == "Y"`, and
2. `Teacher` is present and not `n/a`, and
3. `Teacher` has a row in the `Zoom` sheet.

Rows failing any condition are silently skipped (no warning) — this is expected steady-state
behaviour (e.g. self-study lessons with `Teacher = n/a`), not an error.

## Period resolution

The tool generates events for one period at a time, resolved from a `--period` value plus a
reference date (`--date`, default: today, local time):

- `current-day` (default): just the reference date. Only `Schedule` rows whose `Day` matches the
  reference date's own weekday are considered — i.e. "today's schedule."
- `current-week`: the Monday–Sunday week containing the reference date. Each `Schedule` row's
  `Day` maps to the concrete date of that weekday in the resolved week.
- Future: `next-week`, `month`, a custom date range. Not implemented yet; `period.py` is the
  single place to add them.

## Output

One `.ics` file (`VCALENDAR`) containing:

- `X-WR-CALNAME`: the distinct `Calendar` values found, comma-joined.
- One `VEVENT` per included row for the resolved period, with:
  - `SUMMARY`: `Lesson`.
  - `DTSTART`/`DTEND`: date (from the period) + `Start Time`/`End Time`, in the local machine's
    timezone.
  - `DESCRIPTION`: teacher, calendar, and the raw pasted Zoom invite text, verbatim. No
    `LOCATION` field is set — the tool doesn't parse a URL out of the invite text.
  - `CATEGORIES`: `[Calendar, Type]`.
  - `UID`: deterministic (derived from calendar + date + lesson + start time), so re-running the
    tool for the same week and re-importing updates existing events rather than duplicating them.

## Output filename

When `--output` isn't given, the file is written to the current directory as:

```
Zoom_Schedule_<calendars>_<Day|Week>_<date>.ics
```

- `<calendars>`: the distinct `Calendar` values of the events actually included in this run
  (same period + eligibility filtering as the events themselves — not every calendar mentioned
  anywhere in the workbook), sorted and dash-joined, e.g. `Vasya` or `Other-Vasya`. Falls back to
  `Schedule` if no events were included. Non-filename-safe characters are replaced with `_`.
- `Day` for `current-day`, `Week` for `current-week` (see `PERIOD_LABELS` in `period.py`).
- `<date>`: the resolved reference date, `YYYY-MM-DD`.

Example: `Zoom_Schedule_Vasya_Day_2026-09-18.ics`.

## CLI

```
zoom-ics --input SCHEDULE.xlsx [--output OUT.ics] [--period current-day|current-week] [--date YYYY-MM-DD]
```

Also runnable without installing via `./zoom-ics` (same options).

## Explicitly out of scope for v1

- A `--calendar NAME` filter (all calendars are included; may be added later).
- Any period other than `current-day`/`current-week`.
- A UI beyond the CLI.
- Publishing/hosting the generated `.ics` (e.g. a public URL for calendar subscription).
