# zoom-ics

Generates Google Calendar `.ics` files from a human-readable `.xlsx` schedule, attaching each
teacher's Zoom invite text from a separate directory sheet. 

AI generated/collaborated.

## Input format

The source workbook has two sheets:

- **Schedule** — columns `Day, Lesson, Type, Active, Start Time, End Time, Teacher, Calendar`.
  - `Day` is a weekday abbreviation (`Mon`..`Sun`); any row whose `Day` isn't one of these is
    ignored, so a legend/notes block can live at the bottom of the sheet.
  - `Active` must be `Y` for a row to be considered.
  - `Teacher` is either a name (looked up in the Zoom sheet) or `n/a` for lessons with no live
    session.
  - `Calendar` groups rows (e.g. by student); all calendars found in the sheet are included.
- **Zoom** — columns `Teacher, Description`, where `Description` is a pasted Zoom invite. It's
  used verbatim in the generated event — not parsed for a URL/meeting ID/passcode.

An event is generated only when its row is `Active=Y`, has a real `Teacher` (not `n/a`), and that
teacher has a row in the Zoom sheet.

See [tests/data/Schedule_DB_1.xlsx](tests/data/Schedule_DB_1.xlsx) for a worked example (fake
teacher names and Zoom credentials):

```bash
uv run zoom-ics --input tests/data/Schedule_DB_1.xlsx --period current-week --date 2026-09-08
```

## Install

With [uv](https://docs.astral.sh/uv/) (recommended — no separate install step needed, see
[Usage](#usage)):

```bash
uv sync --extra dev
```

Or with `pip`:

```bash
pip install -e ".[dev]"
```

## Usage

`uv run` creates/updates `.venv` and installs the project automatically the first time you use
it, so there's no separate install step:

```bash
uv run zoom-ics --input schedule.xlsx
```

Or run the standalone shebang script the same way:

```bash
uv run ./zoom-ics --input schedule.xlsx
```

Without `uv`, either activate a `pip install -e`'d virtualenv and run `zoom-ics ...` /
`./zoom-ics ...` directly, or run `./zoom-ics ...` with any Python that already has the
dependencies installed.

Options:

- `--input, -i` — path to the source `.xlsx` file (required).
- `--output, -o` — path to write the `.ics` file. Defaults to
  `Zoom_Schedule_<calendars>_<Day|Week>_<date>.ics` in the current directory, e.g.
  `Zoom_Schedule_Vasya_Day_2026-09-18.ics`, or `Zoom_Schedule_Other-Vasya_Week_2026-09-18.ics`
  when more than one `Calendar` value is included. `<calendars>` lists only the calendars that
  actually have events in this run, dash-joined.
- `--period` — which period to generate: `current-day` (default, today only) or `current-week`.
- `--date` — reference date (`YYYY-MM-DD`) used to resolve the period; defaults to today.

Event times are written in the local machine's timezone.

## Development

With `uv` (installs the `dev` extra automatically):

```bash
uv run --extra dev pytest
```

Or with `pip`:

```bash
pip install -e ".[dev]"
pytest
```

See [.ai/context.md](.ai/context.md) for architecture notes, [.ai/spec.md](.ai/spec.md) for the
full functional spec, and [.ai/tasks.md](.ai/tasks.md) for the current task breakdown.
