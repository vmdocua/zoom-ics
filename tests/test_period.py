from datetime import date

import pytest

from docsultant.zoom_ics.period import resolve_period


@pytest.mark.parametrize(
    "reference",
    [
        date(2026, 9, 8),  # a Tuesday
        date(2026, 9, 7),  # the Monday of that same week
        date(2026, 9, 13),  # the Sunday of that same week
    ],
)
def test_current_week_always_resolves_to_same_monday_to_sunday(reference: date):
    dates = resolve_period("current-week", reference)

    assert dates["Mon"] == date(2026, 9, 7)
    assert dates["Tue"] == date(2026, 9, 8)
    assert dates["Wed"] == date(2026, 9, 9)
    assert dates["Thu"] == date(2026, 9, 10)
    assert dates["Fri"] == date(2026, 9, 11)
    assert dates["Sat"] == date(2026, 9, 12)
    assert dates["Sun"] == date(2026, 9, 13)


def test_unsupported_period_raises():
    with pytest.raises(ValueError):
        resolve_period("next-week", date(2026, 9, 8))


def test_current_day_resolves_to_reference_date_only():
    dates = resolve_period("current-day", date(2026, 9, 8))  # a Tuesday

    assert dates == {"Tue": date(2026, 9, 8)}


def test_current_day_uses_matching_weekday_for_each_reference_date():
    assert resolve_period("current-day", date(2026, 9, 7)) == {"Mon": date(2026, 9, 7)}
    assert resolve_period("current-day", date(2026, 9, 13)) == {"Sun": date(2026, 9, 13)}
