"""Unit tests for hard constraint evaluators and incremental search consistency checking.

Tests TRD TC-HC-1, HC-001..HC-010, and DD-025/DD-026.
"""

from pathlib import Path
import pytest

from src.csp.constraints import (
    ClassNonOverlapConstraint,
    RoomCapacityConstraint,
    RoomNonOverlapConstraint,
    RoomTypeConstraint,
    TeacherAvailabilityConstraint,
    TeacherNonOverlapConstraint,
    TeacherWorkloadConstraint,
    is_assignment_consistent,
)
from src.csp.domains import SlotValue
from src.csp.models import (
    Class,
    Dataset,
    RequirementInput,
    Room,
    ScheduledSession,
    SlotRef,
    Subject,
    Teacher,
    Timetable,
)
from src.csp.variables import SessionVariable


@pytest.fixture
def base_dataset():
    return Dataset(
        dataset_id="test_dataset",
        description="Dataset for testing constraints",
        days=5,
        periods_per_day=6,
        lunch_period=4,
        classes=[
            Class(class_id="C1", name="Class 1", size=30),
            Class(class_id="C2", name="Class 2", size=35),
        ],
        teachers=[
            Teacher(
                teacher_id="T1",
                name="Teacher 1",
                subjects_qualified=["MATH", "PHY"],
                unavailable_slots=[SlotRef(day=0, period=1)],
                max_daily_periods=3,
                max_weekly_periods=10,
            ),
            Teacher(
                teacher_id="T2",
                name="Teacher 2",
                subjects_qualified=["ENG"],
            ),
        ],
        subjects=[
            Subject(subject_id="MATH", name="Math", requires_room_type="lecture"),
            Subject(subject_id="PHY", name="Physics", requires_room_type="lab", is_lab=True),
            Subject(subject_id="ENG", name="English", requires_room_type="lecture"),
        ],
        rooms=[
            Room(room_id="R101", capacity=35, room_type="lecture"),
            Room(room_id="R102", capacity=25, room_type="lecture"),  # small
            Room(room_id="LAB1", capacity=40, room_type="lab"),
        ],
        requirements=[
            RequirementInput(class_id="C1", subject_id="MATH", teacher_id="T1", weekly_periods=1),
            RequirementInput(class_id="C2", subject_id="MATH", teacher_id="T1", weekly_periods=1),
        ],
    )


def test_tc_hc_1_teacher_non_overlap(base_dataset):
    """TRD TC-HC-1: Two sessions with the same teacher in the same slot.

    Expected: HC-001 evaluator returns exactly 1 Violation with both session_ids.
    """
    s1 = ScheduledSession(
        requirement_id="REQ-C1-MATH-01",
        day=1,
        start_period=2,
        duration_periods=1,
        room_id="R101",
        teacher_id="T1",
        class_id="C1",
        subject_id="MATH",
    )
    s2 = ScheduledSession(
        requirement_id="REQ-C2-MATH-01",
        day=1,
        start_period=2,
        duration_periods=1,
        room_id="LAB1",
        teacher_id="T1",  # Same teacher, same day 1 period 2
        class_id="C2",
        subject_id="MATH",
    )

    timetable = Timetable(
        timetable_id="tb_1",
        dataset_id=base_dataset.dataset_id,
        scheduled_sessions=[s1, s2],
    )

    hc001 = TeacherNonOverlapConstraint()
    violations = hc001.evaluate(timetable, base_dataset)

    assert len(violations) == 1
    v = violations[0]
    assert v.constraint_id == "HC-001"
    assert v.kind == "hard"
    assert "T1" in v.resource_ids["teacher_id"]
    assert "REQ-C1-MATH-01" in v.session_ids
    assert "REQ-C2-MATH-01" in v.session_ids


def test_class_non_overlap(base_dataset):
    """HC-002: Two sessions for the same class in the same slot."""
    s1 = ScheduledSession(
        requirement_id="REQ-C1-MATH-01",
        day=2,
        start_period=3,
        duration_periods=1,
        room_id="R101",
        teacher_id="T1",
        class_id="C1",
        subject_id="MATH",
    )
    s2 = ScheduledSession(
        requirement_id="REQ-C1-ENG-01",
        day=2,
        start_period=3,
        duration_periods=1,
        room_id="LAB1",
        teacher_id="T2",
        class_id="C1",  # Same class C1, same slot
        subject_id="ENG",
    )

    timetable = Timetable(
        timetable_id="tb_2",
        dataset_id=base_dataset.dataset_id,
        scheduled_sessions=[s1, s2],
    )

    hc002 = ClassNonOverlapConstraint()
    violations = hc002.evaluate(timetable, base_dataset)

    assert len(violations) == 1
    assert violations[0].constraint_id == "HC-002"
    assert violations[0].resource_ids["class_id"] == "C1"


def test_room_non_overlap(base_dataset):
    """HC-003: Two sessions in the same room in the same slot."""
    s1 = ScheduledSession(
        requirement_id="REQ-C1-MATH-01",
        day=3,
        start_period=1,
        duration_periods=1,
        room_id="R101",
        teacher_id="T1",
        class_id="C1",
        subject_id="MATH",
    )
    s2 = ScheduledSession(
        requirement_id="REQ-C2-ENG-01",
        day=3,
        start_period=1,
        duration_periods=1,
        room_id="R101",  # Same room R101, same slot
        teacher_id="T2",
        class_id="C2",
        subject_id="ENG",
    )

    timetable = Timetable(
        timetable_id="tb_3",
        dataset_id=base_dataset.dataset_id,
        scheduled_sessions=[s1, s2],
    )

    hc003 = RoomNonOverlapConstraint()
    violations = hc003.evaluate(timetable, base_dataset)

    assert len(violations) == 1
    assert violations[0].constraint_id == "HC-003"
    assert violations[0].resource_ids["room_id"] == "R101"


def test_room_capacity_violation(base_dataset):
    """HC-004: Class size 30 placed in room with capacity 25."""
    s = ScheduledSession(
        requirement_id="REQ-C1-MATH-01",
        day=0,
        start_period=2,
        duration_periods=1,
        room_id="R102",  # Capacity 25, C1 size is 30
        teacher_id="T1",
        class_id="C1",
        subject_id="MATH",
    )
    timetable = Timetable(
        timetable_id="tb_4",
        dataset_id=base_dataset.dataset_id,
        scheduled_sessions=[s],
    )

    hc004 = RoomCapacityConstraint()
    violations = hc004.evaluate(timetable, base_dataset)

    assert len(violations) == 1
    assert violations[0].constraint_id == "HC-004"


def test_room_type_violation(base_dataset):
    """HC-005: Physics requiring lab placed in lecture hall."""
    s = ScheduledSession(
        requirement_id="REQ-C1-PHY-01",
        day=0,
        start_period=2,
        duration_periods=1,
        room_id="R101",  # lecture hall, PHY requires 'lab'
        teacher_id="T1",
        class_id="C1",
        subject_id="PHY",
    )
    timetable = Timetable(
        timetable_id="tb_5",
        dataset_id=base_dataset.dataset_id,
        scheduled_sessions=[s],
    )

    hc005 = RoomTypeConstraint()
    violations = hc005.evaluate(timetable, base_dataset)

    assert len(violations) == 1
    assert violations[0].constraint_id == "HC-005"


def test_teacher_availability_violation(base_dataset):
    """HC-006: Teacher T1 assigned to Day 0 Period 1 where T1 is unavailable."""
    s = ScheduledSession(
        requirement_id="REQ-C1-MATH-01",
        day=0,
        start_period=1,  # T1 unavailable slot
        duration_periods=1,
        room_id="R101",
        teacher_id="T1",
        class_id="C1",
        subject_id="MATH",
    )
    timetable = Timetable(
        timetable_id="tb_6",
        dataset_id=base_dataset.dataset_id,
        scheduled_sessions=[s],
    )

    hc006 = TeacherAvailabilityConstraint()
    violations = hc006.evaluate(timetable, base_dataset)

    assert len(violations) == 1
    assert violations[0].constraint_id == "HC-006"


def test_teacher_daily_workload_violation(base_dataset):
    """HC-008: T1 has max_daily_periods=3. Assign 4 periods on day 1."""
    sessions = [
        ScheduledSession(
            requirement_id=f"REQ-T1-{p}",
            day=1,
            start_period=p,
            duration_periods=1,
            room_id=f"R10{p}",
            teacher_id="T1",
            class_id=f"C{p}",
            subject_id="MATH",
        )
        for p in [1, 2, 3, 5]  # 4 periods on day 1
    ]
    timetable = Timetable(
        timetable_id="tb_7",
        dataset_id=base_dataset.dataset_id,
        scheduled_sessions=sessions,
    )

    hc008 = TeacherWorkloadConstraint()
    violations = hc008.evaluate(timetable, base_dataset)

    assert len(violations) >= 1
    assert any(v.constraint_id == "HC-008" and "max_daily_periods" in v.message for v in violations)


def test_incremental_consistency_check(base_dataset):
    """Verify is_assignment_consistent prevents teacher, class, and room collisions."""
    var1 = SessionVariable(requirement_id="REQ-1", class_id="C1", subject_id="MATH", teacher_id="T1")
    var2 = SessionVariable(requirement_id="REQ-2", class_id="C2", subject_id="MATH", teacher_id="T1")  # same teacher
    var3 = SessionVariable(requirement_id="REQ-3", class_id="C1", subject_id="ENG", teacher_id="T2")   # same class
    var4 = SessionVariable(requirement_id="REQ-4", class_id="C2", subject_id="ENG", teacher_id="T2")   # disjoint

    var_map = {v.requirement_id: v for v in [var1, var2, var3, var4]}

    # var1 is assigned to (Day 1, Period 2, Room R101)
    assignment = {"REQ-1": SlotValue(day=1, start_period=2, room_id="R101")}

    # var2 (same teacher) attempting same slot -> should be inconsistent
    assert not is_assignment_consistent(
        var2,
        SlotValue(day=1, start_period=2, room_id="LAB1"),
        assignment,
        var_map,
        base_dataset,
    )

    # var3 (same class) attempting same slot -> should be inconsistent
    assert not is_assignment_consistent(
        var3,
        SlotValue(day=1, start_period=2, room_id="LAB1"),
        assignment,
        var_map,
        base_dataset,
    )

    # var4 (different class, different teacher) attempting same room -> should be inconsistent
    assert not is_assignment_consistent(
        var4,
        SlotValue(day=1, start_period=2, room_id="R101"),
        assignment,
        var_map,
        base_dataset,
    )

    # var4 attempting completely different slot/room -> should be consistent
    assert is_assignment_consistent(
        var4,
        SlotValue(day=1, start_period=3, room_id="R101"),
        assignment,
        var_map,
        base_dataset,
    )
