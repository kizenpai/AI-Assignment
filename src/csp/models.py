"""Domain models and data structures for the AI-Based Timetable Scheduler.

Implements TRD Section F (Domain Model and Data Structures):
- SlotRef: Discrete (day, period) time slot representation.
- Class: Student cohort / group.
- Teacher: Faculty entity with availability, workload limits, and preferences.
- Room: Physical classroom / lab with capacity and type.
- Subject: Course with optional room-type requirement and lab indicator.
- RequirementInput: High-level weekly requirement specification.
- RequiredSession: Atomic CSP scheduling variable (expanded per DD-008).
- ScheduledSession: Concrete timetable assignment.
- Timetable: Complete or partial schedule artifact.
- Dataset: Top-level timetable specification container.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple


@dataclass(frozen=True)
class SlotRef:
    """Discrete time slot reference (day, period).

    Conforms to TRD F.1.5 & DD-007:
    - day: 0-indexed (e.g., 0=Monday, 4=Friday).
    - period: 1-indexed (e.g., 1=Period 1, 6=Period 6).
    """

    day: int
    period: int

    def as_tuple(self) -> Tuple[int, int]:
        return (self.day, self.period)

    def to_dict(self) -> Dict[str, int]:
        return {"day": self.day, "period": self.period}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SlotRef":
        return cls(day=int(data["day"]), period=int(data["period"]))

    def __str__(self) -> str:
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day_str = days[self.day] if 0 <= self.day < len(days) else f"Day {self.day}"
        return f"{day_str} P{self.period}"


@dataclass
class Class:
    """Student cohort / class group (TRD F.1.1)."""

    class_id: str
    name: str
    size: int
    calendar_id: str = "default"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Class":
        return cls(
            class_id=str(data["class_id"]).strip(),
            name=str(data["name"]).strip(),
            size=int(data["size"]),
            calendar_id=str(data.get("calendar_id", "default")).strip(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "class_id": self.class_id,
            "name": self.name,
            "size": self.size,
            "calendar_id": self.calendar_id,
        }


@dataclass
class Teacher:
    """Faculty member (TRD F.1.2 & DD-006).

    Availability is represented sparsely via `unavailable_slots` (DD-006).
    """

    teacher_id: str
    name: str
    subjects_qualified: List[str] = field(default_factory=list)
    unavailable_slots: List[SlotRef] = field(default_factory=list)
    max_daily_periods: Optional[int] = None
    max_weekly_periods: Optional[int] = None
    preferred_slots: List[SlotRef] = field(default_factory=list)
    undesired_slots: List[SlotRef] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Teacher":
        return cls(
            teacher_id=str(data["teacher_id"]).strip(),
            name=str(data["name"]).strip(),
            subjects_qualified=[str(s).strip() for s in data.get("subjects_qualified", [])],
            unavailable_slots=[
                SlotRef.from_dict(s) for s in data.get("unavailable_slots", [])
            ],
            max_daily_periods=(
                int(data["max_daily_periods"])
                if data.get("max_daily_periods") is not None
                else None
            ),
            max_weekly_periods=(
                int(data["max_weekly_periods"])
                if data.get("max_weekly_periods") is not None
                else None
            ),
            preferred_slots=[
                SlotRef.from_dict(s) for s in data.get("preferred_slots", [])
            ],
            undesired_slots=[
                SlotRef.from_dict(s) for s in data.get("undesired_slots", [])
            ],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "teacher_id": self.teacher_id,
            "name": self.name,
            "subjects_qualified": list(self.subjects_qualified),
            "unavailable_slots": [s.to_dict() for s in self.unavailable_slots],
            "max_daily_periods": self.max_daily_periods,
            "max_weekly_periods": self.max_weekly_periods,
            "preferred_slots": [s.to_dict() for s in self.preferred_slots],
            "undesired_slots": [s.to_dict() for s in self.undesired_slots],
        }
        


@dataclass
class Room:
    """Physical instructional space (TRD F.1.3)."""

    room_id: str
    capacity: int
    room_type: str = "lecture"
    unavailable_slots: List[SlotRef] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Room":
        return cls(
            room_id=str(data["room_id"]).strip(),
            capacity=int(data["capacity"]),
            room_type=str(data.get("room_type", "lecture")).strip(),
            unavailable_slots=[
                SlotRef.from_dict(s) for s in data.get("unavailable_slots", [])
            ],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "room_id": self.room_id,
            "capacity": self.capacity,
            "room_type": self.room_type,
            "unavailable_slots": [s.to_dict() for s in self.unavailable_slots],
        }


@dataclass
class Subject:
    """Course / Subject definition (TRD F.1.4)."""

    subject_id: str
    name: str
    requires_room_type: Optional[str] = None
    is_lab: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Subject":
        req_room = data.get("requires_room_type")
        return cls(
            subject_id=str(data["subject_id"]).strip(),
            name=str(data["name"]).strip(),
            requires_room_type=str(req_room).strip() if req_room else None,
            is_lab=bool(data.get("is_lab", False)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "name": self.name,
            "requires_room_type": self.requires_room_type,
            "is_lab": self.is_lab,
        }


@dataclass
class RequirementInput:
    """High-level weekly requirement specification from input JSON (TRD F.2.7)."""

    class_id: str
    subject_id: str
    teacher_id: str
    weekly_periods: int
    duration_periods: int = 1
    consecutive_required: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RequirementInput":
        return cls(
            class_id=str(data["class_id"]).strip(),
            subject_id=str(data["subject_id"]).strip(),
            teacher_id=str(data["teacher_id"]).strip(),
            weekly_periods=int(data["weekly_periods"]),
            duration_periods=int(data.get("duration_periods", 1)),
            consecutive_required=bool(data.get("consecutive_required", False)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "class_id": self.class_id,
            "subject_id": self.subject_id,
            "teacher_id": self.teacher_id,
            "weekly_periods": self.weekly_periods,
            "duration_periods": self.duration_periods,
            "consecutive_required": self.consecutive_required,
        }


@dataclass
class RequiredSession:
    """Atomic required teaching session / CSP variable (TRD F.1.6 & DD-008).

    Expanded at dataset-load time from RequirementInput so each scheduled unit
    maps to exactly one CSP variable.
    """

    requirement_id: str  # e.g., "REQ-C1-MATH-01"
    class_id: str
    subject_id: str
    teacher_id: str
    duration_periods: int = 1
    consecutive_required: bool = False
    occurrence_index: int = 1
    occurrence_total: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "class_id": self.class_id,
            "subject_id": self.subject_id,
            "teacher_id": self.teacher_id,
            "duration_periods": self.duration_periods,
            "consecutive_required": self.consecutive_required,
            "occurrence_index": self.occurrence_index,
            "occurrence_total": self.occurrence_total,
        }


@dataclass
class ScheduledSession:
    """Concrete assignment of a RequiredSession to a time slot and room (TRD F.1.7)."""

    requirement_id: str
    day: int
    start_period: int
    duration_periods: int
    room_id: str
    teacher_id: str
    class_id: str
    subject_id: str

    @property
    def periods(self) -> List[int]:
        """List of 1-indexed period numbers occupied by this session."""
        return list(range(self.start_period, self.start_period + self.duration_periods))

    def occupies_slot(self, day: int, period: int) -> bool:
        return self.day == day and self.start_period <= period < self.start_period + self.duration_periods

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "day": self.day,
            "start_period": self.start_period,
            "duration_periods": self.duration_periods,
            "room_id": self.room_id,
            "teacher_id": self.teacher_id,
            "class_id": self.class_id,
            "subject_id": self.subject_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduledSession":
        return cls(
            requirement_id=str(data["requirement_id"]),
            day=int(data["day"]),
            start_period=int(data["start_period"]),
            duration_periods=int(data.get("duration_periods", 1)),
            room_id=str(data["room_id"]),
            teacher_id=str(data["teacher_id"]),
            class_id=str(data["class_id"]),
            subject_id=str(data["subject_id"]),
        )


TimetableStatus = Literal["Valid", "Invalid", "Incomplete", "NoCandidate", "NotEvaluated"]


@dataclass
class Timetable:
    """Container for candidate or verified schedule assignments (TRD F.1.8)."""

    timetable_id: str
    dataset_id: str
    scheduled_sessions: List[ScheduledSession] = field(default_factory=list)
    unscheduled_requirement_ids: List[str] = field(default_factory=list)
    generated_by: str = "manual"
    generated_at: datetime = field(default_factory=datetime.now)
    status: TimetableStatus = "NotEvaluated"

    def get_session_by_requirement(self, requirement_id: str) -> Optional[ScheduledSession]:
        for s in self.scheduled_sessions:
            if s.requirement_id == requirement_id:
                return s
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timetable_id": self.timetable_id,
            "dataset_id": self.dataset_id,
            "scheduled_sessions": [s.to_dict() for s in self.scheduled_sessions],
            "unscheduled_requirement_ids": list(self.unscheduled_requirement_ids),
            "generated_by": self.generated_by,
            "generated_at": self.generated_at.isoformat(),
            "status": self.status,
        }


@dataclass
class Dataset:
    """Complete timetable input dataset (TRD F.2.1).

    Maintains entity registries and expanded required sessions (DD-008).
    """

    dataset_id: str
    description: str
    days: int = 5
    periods_per_day: int = 6
    lunch_period: Optional[int] = 4
    classes: List[Class] = field(default_factory=list)
    teachers: List[Teacher] = field(default_factory=list)
    subjects: List[Subject] = field(default_factory=list)
    rooms: List[Room] = field(default_factory=list)
    requirements: List[RequirementInput] = field(default_factory=list)
    required_sessions: List[RequiredSession] = field(default_factory=list)

    # Entity lookups for fast access
    def get_class(self, class_id: str) -> Optional[Class]:
        return next((c for c in self.classes if c.class_id == class_id), None)

    def get_teacher(self, teacher_id: str) -> Optional[Teacher]:
        return next((t for t in self.teachers if t.teacher_id == teacher_id), None)

    def get_room(self, room_id: str) -> Optional[Room]:
        return next((r for r in self.rooms if r.room_id == room_id), None)

    def get_subject(self, subject_id: str) -> Optional[Subject]:
        return next((s for s in self.subjects if s.subject_id == subject_id), None)

    def get_required_session(self, requirement_id: str) -> Optional[RequiredSession]:
        return next((rs for rs in self.required_sessions if rs.requirement_id == requirement_id), None)

    @property
    def total_required_periods(self) -> int:
        return sum(r.weekly_periods for r in self.requirements)

    @property
    def total_available_slots_per_class(self) -> int:
        # Theoretical periods per class
        return self.days * self.periods_per_day

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "description": self.description,
            "days": self.days,
            "periods_per_day": self.periods_per_day,
            "lunch_period": self.lunch_period,
            "classes": [c.to_dict() for c in self.classes],
            "teachers": [t.to_dict() for t in self.teachers],
            "subjects": [s.to_dict() for s in self.subjects],
            "rooms": [r.to_dict() for r in self.rooms],
            "requirements": [req.to_dict() for req in self.requirements],
        }
