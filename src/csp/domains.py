"""CSP Domain generation and static constraint filtering.

Implements TRD Section G.2 & TC-DOM-1:
- Discrete slot-room value representation: SlotValue(day, start_period, room_id, duration_periods).
- Static pre-filtering (room type, capacity, teacher unavailable slots, lunch period, day boundary).
- Detects DomainWipeoutAtBuildError if a variable has no legal domain values.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

from src.csp.models import Dataset
from src.csp.variables import SessionVariable


class DomainWipeoutAtBuildError(Exception):
    """Raised when static constraints prevent any legal domain value for a variable at build time."""

    def __init__(self, variable_id: str, reason: str):
        super().__init__(f"Domain wipeout for variable '{variable_id}' at build time: {reason}")
        self.variable_id = variable_id
        self.reason = reason


@dataclass(frozen=True)
class SlotValue:
    """A concrete value assignment in a variable's domain.

    Represents assigning a session to a specific day, starting period, and room.
    """

    day: int
    start_period: int
    room_id: str
    duration_periods: int = 1

    @property
    def periods(self) -> List[int]:
        """List of 1-indexed period numbers occupied by this value."""
        return list(range(self.start_period, self.start_period + self.duration_periods))

    def occupies(self, day: int, period: int) -> bool:
        """Check if this assignment occupies a specific (day, period) slot."""
        return self.day == day and self.start_period <= period < self.start_period + self.duration_periods

    def overlaps_in_time(self, other: "SlotValue") -> bool:
        """Check if two slot values overlap in time on the same day."""
        if self.day != other.day:
            return False
        # Two intervals [s1, s1+d1) and [s2, s2+d2) overlap iff s1 < s2+d2 and s2 < s1+d1
        return (
            self.start_period < other.start_period + other.duration_periods
            and other.start_period < self.start_period + self.duration_periods
        )

    def as_tuple(self) -> Tuple[int, int, str]:
        return (self.day, self.start_period, self.room_id)

    def __str__(self) -> str:
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day_str = days[self.day] if 0 <= self.day < len(days) else f"Day {self.day}"
        if self.duration_periods > 1:
            return f"({day_str} P{self.start_period}-P{self.start_period + self.duration_periods - 1}, {self.room_id})"
        return f"({day_str} P{self.start_period}, {self.room_id})"


def build_domains(
    dataset: Dataset,
    variables: List[SessionVariable],
    strict: bool = False,
) -> Dict[str, List[SlotValue]]:
    """Compute the legal domain values for each CSP variable using static constraints (TRD G.2).

    Static filters applied:
    1. Room capacity >= Class size (HC-004).
    2. Room type matches Subject required room type (HC-005).
    3. Block bounds: start_period + duration - 1 <= periods_per_day (TC-DOM-1).
    4. Teacher unavailable slots: no occupied period may overlap teacher blocked slots (HC-006).
    5. Room unavailable slots: no occupied period may overlap room blocked slots.
    6. Lunch break: if lunch_period is set, no occupied period may overlap lunch (HC-009).

    Args:
        dataset: The timetable dataset.
        variables: The list of SessionVariable objects.
        strict: If True, raise DomainWipeoutAtBuildError immediately on an empty domain.

    Returns:
        Dictionary mapping variable requirement_id -> list of legal SlotValue objects.
    """
    domains: Dict[str, List[SlotValue]] = {}

    # Pre-index room unavailable slots: room_id -> set of (day, period)
    room_blocked: Dict[str, Set[Tuple[int, int]]] = {
        r.room_id: {s.as_tuple() for s in r.unavailable_slots} for r in dataset.rooms
    }

    # Pre-index teacher unavailable slots: teacher_id -> set of (day, period)
    teacher_blocked: Dict[str, Set[Tuple[int, int]]] = {
        t.teacher_id: {s.as_tuple() for s in t.unavailable_slots} for t in dataset.teachers
    }

    lunch = dataset.lunch_period

    for var in variables:
        var_domain: List[SlotValue] = []

        cls_obj = dataset.get_class(var.class_id)
        subj_obj = dataset.get_subject(var.subject_id)
        teacher_id = var.teacher_id
        duration = var.duration_periods

        class_size = cls_obj.size if cls_obj else 0
        req_room_type = subj_obj.requires_room_type if subj_obj else None
        t_blocked = teacher_blocked.get(teacher_id, set())

        # Filter compatible rooms statically
        compatible_rooms = [
            r for r in dataset.rooms
            if r.capacity >= class_size
            and (req_room_type is None or r.room_type == req_room_type)
        ]

        if not compatible_rooms and strict:
            raise DomainWipeoutAtBuildError(
                var.requirement_id,
                f"No room satisfies capacity >= {class_size} and room_type = '{req_room_type}'"
            )

        for room in compatible_rooms:
            r_blocked = room_blocked.get(room.room_id, set())

            for day in range(dataset.days):
                # Ensure session fits within the day's declared periods (TC-DOM-1)
                max_start = dataset.periods_per_day - duration + 1
                for start_p in range(1, max_start + 1):
                    session_periods = range(start_p, start_p + duration)

                    # Check lunch break conflict (HC-009)
                    if lunch is not None and lunch in session_periods:
                        continue

                    # Check teacher availability (HC-006)
                    if any((day, p) in t_blocked for p in session_periods):
                        continue

                    # Check room availability
                    if any((day, p) in r_blocked for p in session_periods):
                        continue

                    # Passed all static checks
                    var_domain.append(
                        SlotValue(
                            day=day,
                            start_period=start_p,
                            room_id=room.room_id,
                            duration_periods=duration,
                        )
                    )

        if not var_domain and strict:
            raise DomainWipeoutAtBuildError(
                var.requirement_id,
                f"Static availability and boundary constraints left zero legal slots for {var}."
            )

        domains[var.requirement_id] = var_domain

    return domains
