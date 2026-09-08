"""Data transfer objects for the two source sheets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time

#: Weekday abbreviations recognised in the "Day" column, in week order.
WEEKDAYS: tuple[str, ...] = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

_NOT_ASSIGNED = "n/a"
_ACTIVE_YES = "Y"


@dataclass(frozen=True, slots=True)
class ScheduleEntry:
    """One row of the "Schedule" sheet."""

    day: str
    lesson: str
    type: str
    active: str
    start_time: time
    end_time: time
    teacher: str
    calendar: str

    @property
    def is_active(self) -> bool:
        return self.active.strip().upper() == _ACTIVE_YES

    @property
    def has_teacher(self) -> bool:
        teacher = self.teacher.strip().lower()
        return bool(teacher) and teacher != _NOT_ASSIGNED


@dataclass(frozen=True, slots=True)
class ZoomEntry:
    """One row of the "Zoom" sheet: a teacher and their pasted Zoom invite text."""

    teacher: str
    description: str
