"""Hard constraint definitions and evaluators for the AI Timetable Scheduler.

Implements TRD Section G.4, Section I (Constraint Details), and DD-025/DD-026:
- Uniform Violation dataclass and Constraint protocol.
- Authoritative implementations of HC-001 through HC-010.
- Pairwise conflict counting policy per DD-026.
- Fast incremental consistency check (is_assignment_consistent) for search algorithms.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from typing import Any, Dict, List, Literal, Optional, Protocol, Set, Tuple

from src.csp.domains import SlotValue
from src.csp.models import Dataset, ScheduledSession, Timetable
from src.csp.variables import SessionVariable


@dataclass
class Violation:
    """Represents a single constraint violation (TRD I.1)."""

    constraint_id: str  # e.g., "HC-001", "SC-001"
    kind: Literal["hard", "soft"]
    message: str
    session_ids: List[str]  # Affected requirement IDs
    resource_ids: Dict[str, str]  # e.g., {"teacher_id": "T1", "day": "1", "period": "2"}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "constraint_id": self.constraint_id,
            "kind": self.kind,
            "message": self.message,
            "session_ids": list(self.session_ids),
            "resource_ids": dict(self.resource_ids),
        }

    def __str__(self) -> str:
        res = ", ".join(f"{k}={v}" for k, v in self.resource_ids.items())
        return f"[{self.constraint_id}] {self.message} ({res}) [sessions: {', '.join(self.session_ids)}]"


class Constraint(Protocol):
    """Protocol for hard and soft constraint evaluators (TRD I.1)."""

    constraint_id: str
    kind: Literal["hard", "soft"]

    def evaluate(self, timetable: Timetable, dataset: Dataset) -> List[Violation]:
        ...


# ============================================================================
# HC-001: Teacher Non-Overlap
# ============================================================================
class TeacherNonOverlapConstraint:
    """HC-001: A teacher cannot teach more than one session at the same time."""

    constraint_id: str = "HC-001"
    kind: Literal["hard", "soft"] = "hard"

    def evaluate(self, timetable: Timetable, dataset: Dataset) -> List[Violation]:
        violations: List[Violation] = []
        # Group sessions by (teacher_id, day, period)
        slot_map: Dict[Tuple[str, int, int], List[ScheduledSession]] = defaultdict(list)

        for s in timetable.scheduled_sessions:
            for p in s.periods:
                slot_map[(s.teacher_id, s.day, p)].append(s)

        for (teacher_id, day, period), sessions in slot_map.items():
            if len(sessions) > 1:
                # Pairwise reporting per DD-026
                for s1, s2 in combinations(sessions, 2):
                    violations.append(
                        Violation(
                            constraint_id=self.constraint_id,
                            kind="hard",
                            message=f"Teacher '{teacher_id}' is double-booked on day {day}, period {period}.",
                            session_ids=[s1.requirement_id, s2.requirement_id],
                            resource_ids={"teacher_id": teacher_id, "day": str(day), "period": str(period)},
                        )
                    )
        return violations


# ============================================================================
# HC-002: Class Non-Overlap
# ============================================================================
class ClassNonOverlapConstraint:
    """HC-002: A class cannot attend more than one session at the same time."""

    constraint_id: str = "HC-002"
    kind: Literal["hard", "soft"] = "hard"

    def evaluate(self, timetable: Timetable, dataset: Dataset) -> List[Violation]:
        violations: List[Violation] = []
        slot_map: Dict[Tuple[str, int, int], List[ScheduledSession]] = defaultdict(list)

        for s in timetable.scheduled_sessions:
            for p in s.periods:
                slot_map[(s.class_id, s.day, p)].append(s)

        for (class_id, day, period), sessions in slot_map.items():
            if len(sessions) > 1:
                for s1, s2 in combinations(sessions, 2):
                    violations.append(
                        Violation(
                            constraint_id=self.constraint_id,
                            kind="hard",
                            message=f"Class '{class_id}' has overlapping sessions on day {day}, period {period}.",
                            session_ids=[s1.requirement_id, s2.requirement_id],
                            resource_ids={"class_id": class_id, "day": str(day), "period": str(period)},
                        )
                    )
        return violations


# ============================================================================
# HC-003: Room Non-Overlap
# ============================================================================
class RoomNonOverlapConstraint:
    """HC-003: A room cannot host more than one session at the same time."""

    constraint_id: str = "HC-003"
    kind: Literal["hard", "soft"] = "hard"

    def evaluate(self, timetable: Timetable, dataset: Dataset) -> List[Violation]:
        violations: List[Violation] = []
        slot_map: Dict[Tuple[str, int, int], List[ScheduledSession]] = defaultdict(list)

        for s in timetable.scheduled_sessions:
            for p in s.periods:
                slot_map[(s.room_id, s.day, p)].append(s)

        for (room_id, day, period), sessions in slot_map.items():
            if len(sessions) > 1:
                for s1, s2 in combinations(sessions, 2):
                    violations.append(
                        Violation(
                            constraint_id=self.constraint_id,
                            kind="hard",
                            message=f"Room '{room_id}' is double-booked on day {day}, period {period}.",
                            session_ids=[s1.requirement_id, s2.requirement_id],
                            resource_ids={"room_id": room_id, "day": str(day), "period": str(period)},
                        )
                    )
        return violations


# ============================================================================
# HC-004: Room Capacity
# ============================================================================
class RoomCapacityConstraint:
    """HC-004: Room capacity must be greater than or equal to class size."""

    constraint_id: str = "HC-004"
    kind: Literal["hard", "soft"] = "hard"

    def evaluate(self, timetable: Timetable, dataset: Dataset) -> List[Violation]:
        violations: List[Violation] = []
        for s in timetable.scheduled_sessions:
            room = dataset.get_room(s.room_id)
            cls_obj = dataset.get_class(s.class_id)
            if room and cls_obj and room.capacity < cls_obj.size:
                violations.append(
                    Violation(
                        constraint_id=self.constraint_id,
                        kind="hard",
                        message=(
                            f"Room '{s.room_id}' (capacity {room.capacity}) cannot accommodate "
                            f"class '{s.class_id}' (size {cls_obj.size})."
                        ),
                        session_ids=[s.requirement_id],
                        resource_ids={"room_id": s.room_id, "class_id": s.class_id},
                    )
                )
        return violations


# ============================================================================
# HC-005: Room Type Compatibility
# ============================================================================
class RoomTypeConstraint:
    """HC-005: Room type must match the required room type of the subject."""

    constraint_id: str = "HC-005"
    kind: Literal["hard", "soft"] = "hard"

    def evaluate(self, timetable: Timetable, dataset: Dataset) -> List[Violation]:
        violations: List[Violation] = []
        for s in timetable.scheduled_sessions:
            subj = dataset.get_subject(s.subject_id)
            room = dataset.get_room(s.room_id)
            if subj and room and subj.requires_room_type:
                if room.room_type != subj.requires_room_type:
                    violations.append(
                        Violation(
                            constraint_id=self.constraint_id,
                            kind="hard",
                            message=(
                                f"Subject '{s.subject_id}' requires room type '{subj.requires_room_type}', "
                                f"but room '{s.room_id}' has type '{room.room_type}'."
                            ),
                            session_ids=[s.requirement_id],
                            resource_ids={"room_id": s.room_id, "subject_id": s.subject_id},
                        )
                    )
        return violations


# ============================================================================
# HC-006: Teacher Availability
# ============================================================================
class TeacherAvailabilityConstraint:
    """HC-006: Teachers cannot be scheduled during their declared unavailable slots."""

    constraint_id: str = "HC-006"
    kind: Literal["hard", "soft"] = "hard"

    def evaluate(self, timetable: Timetable, dataset: Dataset) -> List[Violation]:
        violations: List[Violation] = []
        # Pre-index teacher unavailable slots
        teacher_unavail: Dict[str, Set[Tuple[int, int]]] = {
            t.teacher_id: {s.as_tuple() for s in t.unavailable_slots} for t in dataset.teachers
        }

        for s in timetable.scheduled_sessions:
            blocked = teacher_unavail.get(s.teacher_id, set())
            for p in s.periods:
                if (s.day, p) in blocked:
                    violations.append(
                        Violation(
                            constraint_id=self.constraint_id,
                            kind="hard",
                            message=f"Teacher '{s.teacher_id}' is unavailable on day {s.day}, period {p}.",
                            session_ids=[s.requirement_id],
                            resource_ids={"teacher_id": s.teacher_id, "day": str(s.day), "period": str(p)},
                        )
                    )
        return violations


# ============================================================================
# HC-007: Weekly Hours & Completeness
# ============================================================================
class WeeklyHoursConstraint:
    """HC-007: All required sessions must be scheduled, and counts must match requirements."""

    constraint_id: str = "HC-007"
    kind: Literal["hard", "soft"] = "hard"

    def evaluate(self, timetable: Timetable, dataset: Dataset) -> List[Violation]:
        violations: List[Violation] = []

        # 1. Check for unscheduled required sessions
        scheduled_req_ids = {s.requirement_id for s in timetable.scheduled_sessions}
        for req_sess in dataset.required_sessions:
            if req_sess.requirement_id not in scheduled_req_ids:
                violations.append(
                    Violation(
                        constraint_id=self.constraint_id,
                        kind="hard",
                        message=f"Required session '{req_sess.requirement_id}' is not scheduled.",
                        session_ids=[req_sess.requirement_id],
                        resource_ids={"class_id": req_sess.class_id, "subject_id": req_sess.subject_id},
                    )
                )

        # 2. Check total scheduled period count per (class, subject) against weekly requirements
        scheduled_hours: Dict[Tuple[str, str], int] = defaultdict(int)
        for s in timetable.scheduled_sessions:
            scheduled_hours[(s.class_id, s.subject_id)] += s.duration_periods

        for req in dataset.requirements:
            actual = scheduled_hours.get((req.class_id, req.subject_id), 0)
            if actual != req.weekly_periods:
                violations.append(
                    Violation(
                        constraint_id=self.constraint_id,
                        kind="hard",
                        message=(
                            f"Class '{req.class_id}' has {actual} scheduled periods for "
                            f"subject '{req.subject_id}' (required: {req.weekly_periods})."
                        ),
                        session_ids=[f"REQ-{req.class_id}-{req.subject_id}"],
                        resource_ids={"class_id": req.class_id, "subject_id": req.subject_id},
                    )
                )
        return violations


# ============================================================================
# HC-008: Teacher Workload Limits
# ============================================================================
class TeacherWorkloadConstraint:
    """HC-008: Teacher daily and weekly workloads must not exceed configured maximums."""

    constraint_id: str = "HC-008"
    kind: Literal["hard", "soft"] = "hard"

    def evaluate(self, timetable: Timetable, dataset: Dataset) -> List[Violation]:
        violations: List[Violation] = []

        daily_counts: Dict[Tuple[str, int], int] = defaultdict(int)
        weekly_counts: Dict[str, int] = defaultdict(int)

        for s in timetable.scheduled_sessions:
            daily_counts[(s.teacher_id, s.day)] += s.duration_periods
            weekly_counts[s.teacher_id] += s.duration_periods

        for teacher in dataset.teachers:
            tid = teacher.teacher_id

            # Check daily limits
            if teacher.max_daily_periods is not None:
                for day in range(dataset.days):
                    count = daily_counts.get((tid, day), 0)
                    if count > teacher.max_daily_periods:
                        violations.append(
                            Violation(
                                constraint_id=self.constraint_id,
                                kind="hard",
                                message=(
                                    f"Teacher '{tid}' taught {count} periods on day {day}, "
                                    f"exceeding max_daily_periods ({teacher.max_daily_periods})."
                                ),
                                session_ids=[],
                                resource_ids={"teacher_id": tid, "day": str(day)},
                            )
                        )

            # Check weekly limits
            if teacher.max_weekly_periods is not None:
                total = weekly_counts.get(tid, 0)
                if total > teacher.max_weekly_periods:
                    violations.append(
                        Violation(
                            constraint_id=self.constraint_id,
                            kind="hard",
                            message=(
                                f"Teacher '{tid}' taught {total} periods in the week, "
                                f"exceeding max_weekly_periods ({teacher.max_weekly_periods})."
                            ),
                            session_ids=[],
                            resource_ids={"teacher_id": tid},
                        )
                    )
        return violations


# ============================================================================
# HC-009: Mandatory Lunch Break
# ============================================================================
class LunchBreakConstraint:
    """HC-009: No teaching session may be scheduled during the designated lunch period."""

    constraint_id: str = "HC-009"
    kind: Literal["hard", "soft"] = "hard"

    def evaluate(self, timetable: Timetable, dataset: Dataset) -> List[Violation]:
        violations: List[Violation] = []
        lunch = dataset.lunch_period
        if lunch is None:
            return violations

        for s in timetable.scheduled_sessions:
            if lunch in s.periods:
                violations.append(
                    Violation(
                        constraint_id=self.constraint_id,
                        kind="hard",
                        message=f"Session '{s.requirement_id}' overlaps with mandatory lunch period ({lunch}).",
                        session_ids=[s.requirement_id],
                        resource_ids={"day": str(s.day), "period": str(lunch)},
                    )
                )
        return violations


# ============================================================================
# HC-010: Laboratory Contiguity
# ============================================================================
class LabContiguityConstraint:
    """HC-010: Multi-period block sessions must occupy contiguous periods within a single day."""

    constraint_id: str = "HC-010"
    kind: Literal["hard", "soft"] = "hard"

    def evaluate(self, timetable: Timetable, dataset: Dataset) -> List[Violation]:
        violations: List[Violation] = []
        for s in timetable.scheduled_sessions:
            if s.duration_periods > 1:
                # Check day bounds
                if s.start_period + s.duration_periods - 1 > dataset.periods_per_day:
                    violations.append(
                        Violation(
                            constraint_id=self.constraint_id,
                            kind="hard",
                            message=(
                                f"Multi-period session '{s.requirement_id}' overflows past "
                                f"the end of day (start: {s.start_period}, duration: {s.duration_periods})."
                            ),
                            session_ids=[s.requirement_id],
                            resource_ids={"day": str(s.day), "start_period": str(s.start_period)},
                        )
                    )
        return violations


ALL_HARD_CONSTRAINTS: List[Constraint] = [
    TeacherNonOverlapConstraint(),
    ClassNonOverlapConstraint(),
    RoomNonOverlapConstraint(),
    RoomCapacityConstraint(),
    RoomTypeConstraint(),
    TeacherAvailabilityConstraint(),
    WeeklyHoursConstraint(),
    TeacherWorkloadConstraint(),
    LunchBreakConstraint(),
    LabContiguityConstraint(),
]


# ============================================================================
# Incremental Search Consistency Checker
# ============================================================================
def is_assignment_consistent(
    var: SessionVariable,
    val: SlotValue,
    current_assignment: Dict[str, SlotValue],
    var_map: Dict[str, SessionVariable],
    dataset: Dataset,
) -> bool:
    """Fast incremental consistency check used during Backtracking and Min-Conflicts.

    Tests whether assigning `val` to `var` is consistent with all currently assigned
    variables in `current_assignment`.

    Checks:
    - Teacher overlap (HC-001)
    - Class overlap (HC-002)
    - Room overlap (HC-003)
    - Teacher daily workload limit (HC-008)
    - Teacher weekly workload limit (HC-008)
    """
    teacher = dataset.get_teacher(var.teacher_id)
    t_daily_max = teacher.max_daily_periods if teacher else None
    t_weekly_max = teacher.max_weekly_periods if teacher else None

    daily_teacher_periods = val.duration_periods
    weekly_teacher_periods = val.duration_periods

    for other_id, other_val in current_assignment.items():
        if other_id == var.requirement_id:
            continue

        other_var = var_map[other_id]

        # Check teacher overlap (HC-001)
        if other_var.teacher_id == var.teacher_id:
            if val.overlaps_in_time(other_val):
                return False
            # Accumulate teacher workload
            if other_val.day == val.day:
                daily_teacher_periods += other_val.duration_periods
            weekly_teacher_periods += other_val.duration_periods

        # Check class overlap (HC-002)
        if other_var.class_id == var.class_id:
            if val.overlaps_in_time(other_val):
                return False

        # Check room overlap (HC-003)
        if other_val.room_id == val.room_id:
            if val.overlaps_in_time(other_val):
                return False

    # Check workload bounds
    if t_daily_max is not None and daily_teacher_periods > t_daily_max:
        return False
    if t_weekly_max is not None and weekly_teacher_periods > t_weekly_max:
        return False

    return True
