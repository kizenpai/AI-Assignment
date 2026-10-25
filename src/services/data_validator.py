"""Dataset validation service.

Implements PRD FR-005 and TRD Section C.2 / P.1:
- Structural integrity checks (missing fields, type mismatches).
- Referential integrity checks (dangling foreign keys).
- Duplicate identifier detection.
- Workload and availability bounds validation.
- Distinguishes blocking errors (preventing scheduling) from warnings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Set


class DatasetValidationException(Exception):
    """Raised when an operation requires a valid dataset but blocking errors exist."""

    def __init__(self, message: str, errors: Optional[List["ValidationMessage"]] = None):
        super().__init__(message)
        self.errors = errors or []


@dataclass
class ValidationMessage:
    """Detailed error or warning message for dataset validation."""

    kind: Literal["error", "warning"]
    code: str
    message: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    field: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "code": self.code,
            "message": self.message,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "field": self.field,
        }

    def __str__(self) -> str:
        ctx = ""
        if self.entity_type or self.entity_id:
            ctx = f" [{self.entity_type or ''}:{self.entity_id or ''}]"
        return f"{self.kind.upper()} ({self.code}){ctx}: {self.message}"


@dataclass
class DatasetValidationReport:
    """Complete validation result for a dataset."""

    is_valid: bool
    errors: List[ValidationMessage] = field(default_factory=list)
    warnings: List[ValidationMessage] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    def raise_if_invalid(self) -> None:
        if not self.is_valid:
            msg = f"Dataset validation failed with {len(self.errors)} blocking error(s): " + "; ".join(
                str(e) for e in self.errors[:3]
            )
            if len(self.errors) > 3:
                msg += f" (and {len(self.errors) - 3} more)"
            raise DatasetValidationException(msg, errors=self.errors)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "summary": self.summary,
        }


def validate_dataset_dict(raw: Dict[str, Any]) -> DatasetValidationReport:
    """Validate raw dictionary before or during dataset loading.

    Checks:
    1. Top-level required keys and bounds.
    2. Duplicate IDs for classes, teachers, rooms, subjects.
    3. Missing / invalid attributes within entities.
    4. Referential integrity:
       - Teacher subjects_qualified in subjects
       - Requirement class_id in classes
       - Requirement subject_id in subjects
       - Requirement teacher_id in teachers
       - Teacher qualification for required subject
       - Room capacity and type compatibility for each requirement
    5. SlotRef bounds (day in [0, days-1], period in [1, periods_per_day]).
    6. Teacher / Class workload limits.
    """
    errors: List[ValidationMessage] = []
    warnings: List[ValidationMessage] = []

    if not isinstance(raw, dict):
        return DatasetValidationReport(
            is_valid=False,
            errors=[
                ValidationMessage(
                    kind="error",
                    code="VAL_ROOT_TYPE",
                    message="Dataset root must be a JSON object / dictionary.",
                )
            ],
        )

    # 1. Top-level required fields
    required_top_keys = [
        "dataset_id",
        "description",
        "days",
        "periods_per_day",
        "classes",
        "teachers",
        "subjects",
        "rooms",
        "requirements",
    ]
    for k in required_top_keys:
        if k not in raw:
            errors.append(
                ValidationMessage(
                    kind="error",
                    code="VAL_MISSING_KEY",
                    message=f"Missing required top-level field '{k}'.",
                    field=k,
                )
            )

    dataset_id = str(raw.get("dataset_id", "unknown")).strip()
    days = raw.get("days")
    periods_per_day = raw.get("periods_per_day")
    lunch_period = raw.get("lunch_period")

    if days is not None:
        if not isinstance(days, int) or days <= 0 or days > 7:
            errors.append(
                ValidationMessage(
                    kind="error",
                    code="VAL_INVALID_DAYS",
                    message=f"'days' must be an integer between 1 and 7, got {days}.",
                    field="days",
                )
            )
            days = 5  # fallback for downstream slot checking
    else:
        days = 5

    if periods_per_day is not None:
        if not isinstance(periods_per_day, int) or periods_per_day <= 0 or periods_per_day > 16:
            errors.append(
                ValidationMessage(
                    kind="error",
                    code="VAL_INVALID_PERIODS",
                    message=f"'periods_per_day' must be an integer between 1 and 16, got {periods_per_day}.",
                    field="periods_per_day",
                )
            )
            periods_per_day = 6  # fallback
    else:
        periods_per_day = 6

    if lunch_period is not None:
        if not isinstance(lunch_period, int) or lunch_period < 1 or lunch_period > periods_per_day:
            warnings.append(
                ValidationMessage(
                    kind="warning",
                    code="VAL_INVALID_LUNCH",
                    message=f"'lunch_period' ({lunch_period}) should be within 1 and {periods_per_day}.",
                    field="lunch_period",
                )
            )

    # Helper to check a slot
    def check_slot(slot: Any, context: str, ent_type: str, ent_id: str) -> None:
        if not isinstance(slot, dict) or "day" not in slot or "period" not in slot:
            errors.append(
                ValidationMessage(
                    kind="error",
                    code="VAL_INVALID_SLOT_FORMAT",
                    message=f"Invalid slot format in {context}: expected object with 'day' and 'period'.",
                    entity_type=ent_type,
                    entity_id=ent_id,
                )
            )
            return

        s_day = slot["day"]
        s_per = slot["period"]
        if not isinstance(s_day, int) or s_day < 0 or s_day >= days:
            errors.append(
                ValidationMessage(
                    kind="error",
                    code="VAL_SLOT_DAY_OUT_OF_BOUNDS",
                    message=f"Slot day {s_day} is out of bounds (allowed: 0..{days - 1}) in {context}.",
                    entity_type=ent_type,
                    entity_id=ent_id,
                )
            )
        if not isinstance(s_per, int) or s_per < 1 or s_per > periods_per_day:
            errors.append(
                ValidationMessage(
                    kind="error",
                    code="VAL_SLOT_PERIOD_OUT_OF_BOUNDS",
                    message=f"Slot period {s_per} is out of bounds (allowed: 1..{periods_per_day}) in {context}.",
                    entity_type=ent_type,
                    entity_id=ent_id,
                )
            )

    # 2. Classes validation
    raw_classes = raw.get("classes", [])
    class_ids: Set[str] = set()
    class_sizes: Dict[str, int] = {}
    if not isinstance(raw_classes, list):
        errors.append(
            ValidationMessage(
                kind="error",
                code="VAL_INVALID_CLASSES_TYPE",
                message="'classes' must be a list of class objects.",
                field="classes",
            )
        )
    else:
        for idx, c in enumerate(raw_classes):
            if not isinstance(c, dict):
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_INVALID_CLASS_ENTRY",
                        message=f"Class at index {idx} must be an object.",
                        entity_type="class",
                    )
                )
                continue
            cid = str(c.get("class_id", "")).strip()
            if not cid:
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_EMPTY_CLASS_ID",
                        message=f"Class at index {idx} has an empty 'class_id'.",
                        entity_type="class",
                    )
                )
                continue
            if cid in class_ids:
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_DUPLICATE_CLASS_ID",
                        message=f"Duplicate class_id '{cid}' found.",
                        entity_type="class",
                        entity_id=cid,
                    )
                )
            class_ids.add(cid)

            size = c.get("size")
            if size is None or not isinstance(size, int) or size <= 0:
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_INVALID_CLASS_SIZE",
                        message=f"Class '{cid}' has invalid or non-positive size: {size}.",
                        entity_type="class",
                        entity_id=cid,
                        field="size",
                    )
                )
                class_sizes[cid] = 30
            else:
                class_sizes[cid] = size

    # 3. Subjects validation
    raw_subjects = raw.get("subjects", [])
    subject_ids: Set[str] = set()
    subject_room_types: Dict[str, Optional[str]] = {}
    if not isinstance(raw_subjects, list):
        errors.append(
            ValidationMessage(
                kind="error",
                code="VAL_INVALID_SUBJECTS_TYPE",
                message="'subjects' must be a list of subject objects.",
                field="subjects",
            )
        )
    else:
        for idx, s in enumerate(raw_subjects):
            if not isinstance(s, dict):
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_INVALID_SUBJECT_ENTRY",
                        message=f"Subject at index {idx} must be an object.",
                        entity_type="subject",
                    )
                )
                continue
            sid = str(s.get("subject_id", "")).strip()
            if not sid:
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_EMPTY_SUBJECT_ID",
                        message=f"Subject at index {idx} has an empty 'subject_id'.",
                        entity_type="subject",
                    )
                )
                continue
            if sid in subject_ids:
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_DUPLICATE_SUBJECT_ID",
                        message=f"Duplicate subject_id '{sid}' found.",
                        entity_type="subject",
                        entity_id=sid,
                    )
                )
            subject_ids.add(sid)
            req_room = s.get("requires_room_type")
            subject_room_types[sid] = str(req_room).strip() if req_room else None

    # 4. Rooms validation
    raw_rooms = raw.get("rooms", [])
    room_ids: Set[str] = set()
    room_types: Set[str] = set()
    max_room_capacity = 0
    if not isinstance(raw_rooms, list):
        errors.append(
            ValidationMessage(
                kind="error",
                code="VAL_INVALID_ROOMS_TYPE",
                message="'rooms' must be a list of room objects.",
                field="rooms",
            )
        )
    else:
        for idx, r in enumerate(raw_rooms):
            if not isinstance(r, dict):
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_INVALID_ROOM_ENTRY",
                        message=f"Room at index {idx} must be an object.",
                        entity_type="room",
                    )
                )
                continue
            rid = str(r.get("room_id", "")).strip()
            if not rid:
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_EMPTY_ROOM_ID",
                        message=f"Room at index {idx} has an empty 'room_id'.",
                        entity_type="room",
                    )
                )
                continue
            if rid in room_ids:
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_DUPLICATE_ROOM_ID",
                        message=f"Duplicate room_id '{rid}' found.",
                        entity_type="room",
                        entity_id=rid,
                    )
                )
            room_ids.add(rid)

            cap = r.get("capacity")
            if cap is None or not isinstance(cap, int) or cap <= 0:
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_INVALID_ROOM_CAPACITY",
                        message=f"Room '{rid}' has invalid or non-positive capacity: {cap}.",
                        entity_type="room",
                        entity_id=rid,
                        field="capacity",
                    )
                )
            else:
                max_room_capacity = max(max_room_capacity, cap)

            rtype = str(r.get("room_type", "lecture")).strip()
            room_types.add(rtype)

            for slot in r.get("unavailable_slots", []):
                check_slot(slot, f"room '{rid}' unavailable_slots", "room", rid)

    # 5. Teachers validation
    raw_teachers = raw.get("teachers", [])
    teacher_ids: Set[str] = set()
    teacher_qualified_map: Dict[str, Set[str]] = {}
    teacher_workload_limits: Dict[str, Optional[int]] = {}
    if not isinstance(raw_teachers, list):
        errors.append(
            ValidationMessage(
                kind="error",
                code="VAL_INVALID_TEACHERS_TYPE",
                message="'teachers' must be a list of teacher objects.",
                field="teachers",
            )
        )
    else:
        for idx, t in enumerate(raw_teachers):
            if not isinstance(t, dict):
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_INVALID_TEACHER_ENTRY",
                        message=f"Teacher at index {idx} must be an object.",
                        entity_type="teacher",
                    )
                )
                continue
            tid = str(t.get("teacher_id", "")).strip()
            if not tid:
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_EMPTY_TEACHER_ID",
                        message=f"Teacher at index {idx} has an empty 'teacher_id'.",
                        entity_type="teacher",
                    )
                )
                continue
            if tid in teacher_ids:
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_DUPLICATE_TEACHER_ID",
                        message=f"Duplicate teacher_id '{tid}' found.",
                        entity_type="teacher",
                        entity_id=tid,
                    )
                )
            teacher_ids.add(tid)

            # Subjects qualified referential integrity
            quals = t.get("subjects_qualified", [])
            teacher_qualified_map[tid] = set()
            if not isinstance(quals, list):
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_INVALID_QUALIFICATIONS_TYPE",
                        message=f"Teacher '{tid}' subjects_qualified must be a list.",
                        entity_type="teacher",
                        entity_id=tid,
                    )
                )
            else:
                for q in quals:
                    q_str = str(q).strip()
                    if q_str not in subject_ids:
                        errors.append(
                            ValidationMessage(
                                kind="error",
                                code="VAL_UNKNOWN_QUALIFIED_SUBJECT",
                                message=f"Teacher '{tid}' is qualified for unknown subject '{q_str}'.",
                                entity_type="teacher",
                                entity_id=tid,
                                field="subjects_qualified",
                            )
                        )
                    else:
                        teacher_qualified_map[tid].add(q_str)

            # Slot checks for teacher
            for slot in t.get("unavailable_slots", []):
                check_slot(slot, f"teacher '{tid}' unavailable_slots", "teacher", tid)
            for slot in t.get("preferred_slots", []):
                check_slot(slot, f"teacher '{tid}' preferred_slots", "teacher", tid)
            for slot in t.get("undesired_slots", []):
                check_slot(slot, f"teacher '{tid}' undesired_slots", "teacher", tid)

            # Workload checks
            m_daily = t.get("max_daily_periods")
            if m_daily is not None:
                if not isinstance(m_daily, int) or m_daily <= 0 or m_daily > periods_per_day:
                    errors.append(
                        ValidationMessage(
                            kind="error",
                            code="VAL_INVALID_MAX_DAILY",
                            message=f"Teacher '{tid}' max_daily_periods ({m_daily}) must be between 1 and {periods_per_day}.",
                            entity_type="teacher",
                            entity_id=tid,
                            field="max_daily_periods",
                        )
                    )

            m_weekly = t.get("max_weekly_periods")
            teacher_workload_limits[tid] = m_weekly if isinstance(m_weekly, int) else None
            max_possible_weekly = days * periods_per_day
            if m_weekly is not None:
                if not isinstance(m_weekly, int) or m_weekly <= 0 or m_weekly > max_possible_weekly:
                    errors.append(
                        ValidationMessage(
                            kind="error",
                            code="VAL_INVALID_MAX_WEEKLY",
                            message=f"Teacher '{tid}' max_weekly_periods ({m_weekly}) must be between 1 and {max_possible_weekly}.",
                            entity_type="teacher",
                            entity_id=tid,
                            field="max_weekly_periods",
                        )
                    )

    # 6. Requirements validation
    raw_requirements = raw.get("requirements", [])
    teacher_assigned_hours: Dict[str, int] = {tid: 0 for tid in teacher_ids}
    class_assigned_hours: Dict[str, int] = {cid: 0 for cid in class_ids}

    if not isinstance(raw_requirements, list):
        errors.append(
            ValidationMessage(
                kind="error",
                code="VAL_INVALID_REQUIREMENTS_TYPE",
                message="'requirements' must be a list of requirement objects.",
                field="requirements",
            )
        )
    else:
        for idx, req in enumerate(raw_requirements):
            if not isinstance(req, dict):
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_INVALID_REQUIREMENT_ENTRY",
                        message=f"Requirement at index {idx} must be an object.",
                        entity_type="requirement",
                    )
                )
                continue

            cid = str(req.get("class_id", "")).strip()
            sid = str(req.get("subject_id", "")).strip()
            tid = str(req.get("teacher_id", "")).strip()
            wp = req.get("weekly_periods")
            dp = req.get("duration_periods", 1)

            # Check class reference (FR-005)
            if not cid:
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_REQ_EMPTY_CLASS_ID",
                        message=f"Requirement at index {idx} has an empty 'class_id'.",
                        entity_type="requirement",
                        field="class_id",
                    )
                )
            elif cid not in class_ids:
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_UNKNOWN_CLASS_REF",
                        message=f"Requirement #{idx + 1} references unknown class_id '{cid}'.",
                        entity_type="requirement",
                        entity_id=cid,
                        field="class_id",
                    )
                )

            # Check subject reference (FR-005)
            if not sid:
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_REQ_EMPTY_SUBJECT_ID",
                        message=f"Requirement at index {idx} has an empty 'subject_id'.",
                        entity_type="requirement",
                        field="subject_id",
                    )
                )
            elif sid not in subject_ids:
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_UNKNOWN_SUBJECT_REF",
                        message=f"Requirement #{idx + 1} references unknown subject_id '{sid}'.",
                        entity_type="requirement",
                        entity_id=sid,
                        field="subject_id",
                    )
                )

            # Check teacher reference (FR-005, TC-DV-1)
            if not tid:
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_REQ_EMPTY_TEACHER_ID",
                        message=f"Requirement at index {idx} has an empty 'teacher_id'.",
                        entity_type="requirement",
                        field="teacher_id",
                    )
                )
            elif tid not in teacher_ids:
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_UNKNOWN_TEACHER_REF",
                        message=f"Requirement #{idx + 1} references unknown teacher_id '{tid}'.",
                        entity_type="requirement",
                        entity_id=tid,
                        field="teacher_id",
                    )
                )
            else:
                # Check teacher qualification
                if sid in subject_ids and sid not in teacher_qualified_map.get(tid, set()):
                    errors.append(
                        ValidationMessage(
                            kind="error",
                            code="VAL_TEACHER_NOT_QUALIFIED",
                            message=f"Teacher '{tid}' is not qualified to teach subject '{sid}' for class '{cid}'.",
                            entity_type="requirement",
                            entity_id=tid,
                            field="teacher_id",
                        )
                    )

            # Check weekly_periods
            if wp is None or not isinstance(wp, int) or wp <= 0:
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_INVALID_WEEKLY_PERIODS",
                        message=f"Requirement #{idx + 1} (class '{cid}', subject '{sid}') must have positive 'weekly_periods'.",
                        entity_type="requirement",
                        field="weekly_periods",
                    )
                )
                wp = 1

            # Check duration_periods
            if not isinstance(dp, int) or dp <= 0 or dp > periods_per_day:
                errors.append(
                    ValidationMessage(
                        kind="error",
                        code="VAL_INVALID_DURATION",
                        message=f"Requirement #{idx + 1} duration_periods ({dp}) must be between 1 and {periods_per_day}.",
                        entity_type="requirement",
                        field="duration_periods",
                    )
                )
                dp = 1

            if wp % dp != 0:
                warnings.append(
                    ValidationMessage(
                        kind="warning",
                        code="VAL_DURATION_MISMATCH",
                        message=f"Requirement #{idx + 1} weekly_periods ({wp}) is not evenly divisible by duration_periods ({dp}).",
                        entity_type="requirement",
                        field="duration_periods",
                    )
                )

            # Track assigned periods
            if tid in teacher_assigned_hours:
                teacher_assigned_hours[tid] += wp
            if cid in class_assigned_hours:
                class_assigned_hours[cid] += wp

            # Room feasibility check: Is there ANY room that can fit this class and room_type?
            if cid in class_ids and sid in subject_ids and raw_rooms:
                req_rtype = subject_room_types.get(sid)
                c_size = class_sizes.get(cid, 0)
                matching_rooms = [
                    r for r in raw_rooms
                    if isinstance(r, dict)
                    and (req_rtype is None or str(r.get("room_type", "lecture")).strip() == req_rtype)
                    and int(r.get("capacity", 0)) >= c_size
                ]
                if not matching_rooms:
                    errors.append(
                        ValidationMessage(
                            kind="error",
                            code="VAL_NO_COMPATIBLE_ROOM",
                            message=(
                                f"No compatible room found for class '{cid}' (size {c_size}) "
                                f"and subject '{sid}' (required type: {req_rtype or 'any'})."
                            ),
                            entity_type="requirement",
                            entity_id=f"{cid}-{sid}",
                        )
                    )

    # 7. Aggregate workload sanity checks
    total_slots_per_class = days * periods_per_day
    for cid, total_hrs in class_assigned_hours.items():
        if total_hrs > total_slots_per_class:
            errors.append(
                ValidationMessage(
                    kind="error",
                    code="VAL_CLASS_OVERLOAD",
                    message=(
                        f"Class '{cid}' requires {total_hrs} weekly periods, exceeding "
                        f"the maximum available weekly slots ({total_slots_per_class})."
                    ),
                    entity_type="class",
                    entity_id=cid,
                )
            )

    for tid, total_hrs in teacher_assigned_hours.items():
        m_weekly = teacher_workload_limits.get(tid)
        if m_weekly is not None and total_hrs > m_weekly:
            warnings.append(
                ValidationMessage(
                    kind="warning",
                    code="VAL_TEACHER_WEEKLY_EXCEEDED",
                    message=(
                        f"Teacher '{tid}' is assigned {total_hrs} weekly periods, "
                        f"exceeding max_weekly_periods limit of {m_weekly}."
                    ),
                    entity_type="teacher",
                    entity_id=tid,
                )
            )

    is_valid = len(errors) == 0
    total_req_periods = sum(
        r.get("weekly_periods", 0) for r in raw_requirements if isinstance(r, dict) and isinstance(r.get("weekly_periods"), int)
    )

    summary = {
        "dataset_id": dataset_id,
        "days": days,
        "periods_per_day": periods_per_day,
        "lunch_period": lunch_period,
        "classes_count": len(class_ids),
        "teachers_count": len(teacher_ids),
        "subjects_count": len(subject_ids),
        "rooms_count": len(room_ids),
        "requirements_count": len(raw_requirements) if isinstance(raw_requirements, list) else 0,
        "total_required_periods": total_req_periods,
    }

    return DatasetValidationReport(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        summary=summary,
    )
