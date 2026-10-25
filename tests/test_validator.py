"""Unit tests for the independent validator.

Tests TRD TC-VAL-1, TC-VAL-2, Section J, NFR-003, and NFR-004.
"""

from pathlib import Path
import pytest

from src.csp.models import (
    Class,
    Dataset,
    RequirementInput,
    Room,
    ScheduledSession,
    Subject,
    Teacher,
    Timetable,
)
from src.csp.validator import validate
from src.services.data_loader import load_dataset_from_file


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture
def sample_dataset():
    path = DATA_DIR / "small_dataset.json"
    dataset, _ = load_dataset_from_file(path)
    return dataset


def test_tc_val_1_room_capacity_violation(sample_dataset):
    """TRD TC-VAL-1: A timetable with a known room-capacity violation.

    Expected: status="Invalid", HC-004 present in violation_categories with count 1.
    """
    # Create valid dummy assignments for all required sessions except one has capacity violation
    scheduled = []
    # Assign each session to a distinct slot / room
    for i, req in enumerate(sample_dataset.required_sessions):
        day = (i // 5) % sample_dataset.days
        period = (i % 5) + 1  # 1..5 (avoid lunch at 4 for all except test)
        if period == 4:
            period = 6

        # Purposefully place the FIRST session into R102 with an artificially inflated class size
        # Or place into a tiny room if we add one:
        room_id = "R101"
        if i == 0:
            # R102 has capacity 35. Class C3 has size 32. Let's make room capacity smaller than class
            # We can use R102 and make the session's class size larger
            pass

        scheduled.append(
            ScheduledSession(
                requirement_id=req.requirement_id,
                day=day,
                start_period=period,
                duration_periods=req.duration_periods,
                room_id=room_id,
                teacher_id=req.teacher_id,
                class_id=req.class_id,
                subject_id=req.subject_id,
            )
        )

    # Let's tamper with the first class to have size 50 (max room is 40)
    c1 = sample_dataset.get_class("C1")
    orig_size = c1.size
    c1.size = 50

    try:
        timetable = Timetable(
            timetable_id="val_test_1",
            dataset_id=sample_dataset.dataset_id,
            scheduled_sessions=scheduled,
        )
        report = validate(timetable, sample_dataset)

        assert report.status == "Invalid"
        assert report.is_valid is False
        assert "HC-004" in report.violation_categories
        assert report.violation_categories["HC-004"] >= 1
    finally:
        c1.size = orig_size


def test_tc_val_2_consistent_validation_determinism(sample_dataset):
    """TRD TC-VAL-2 / NFR-003: Same timetable validated twice produces identical report."""
    timetable = Timetable(
        timetable_id="val_test_2",
        dataset_id=sample_dataset.dataset_id,
        scheduled_sessions=[],
    )

    report1 = validate(timetable, sample_dataset)
    report2 = validate(timetable, sample_dataset)

    assert report1.status == report2.status
    assert report1.total_hard_violations == report2.total_hard_violations
    assert report1.violation_categories == report2.violation_categories
    assert report1.total_soft_penalty == report2.total_soft_penalty
    assert len(report1.violations) == len(report2.violations)


def test_incomplete_timetable_status(sample_dataset):
    """An incomplete timetable (missing required sessions) must have status='Incomplete'."""
    # Only schedule 1 session out of 42
    req = sample_dataset.required_sessions[0]
    s = ScheduledSession(
        requirement_id=req.requirement_id,
        day=0,
        start_period=2,
        duration_periods=req.duration_periods,
        room_id="R101",
        teacher_id=req.teacher_id,
        class_id=req.class_id,
        subject_id=req.subject_id,
    )
    timetable = Timetable(
        timetable_id="inc_test",
        dataset_id=sample_dataset.dataset_id,
        scheduled_sessions=[s],
    )

    report = validate(timetable, sample_dataset)
    assert report.status == "Incomplete"
    assert report.is_valid is False


def test_none_timetable_reports_no_candidate(sample_dataset):
    """Validating None produces status='NoCandidate'."""
    report = validate(None, sample_dataset)
    assert report.status == "NoCandidate"
    assert report.is_valid is False


def test_soft_penalty_breakdown_inspection(sample_dataset):
    """Verify soft penalties SC-001..SC-005 are calculated and itemized in report (FR-015)."""
    # Create two sessions with an idle gap between them on Monday for Class C1:
    # Period 1 and Period 3 (Period 2 is an idle gap)
    s1 = ScheduledSession(
        requirement_id="REQ-1",
        day=0,
        start_period=1,
        duration_periods=1,
        room_id="R101",
        teacher_id="T1",
        class_id="C1",
        subject_id="MATH",
    )
    s2 = ScheduledSession(
        requirement_id="REQ-2",
        day=0,
        start_period=3,  # idle gap at period 2!
        duration_periods=1,
        room_id="R101",
        teacher_id="T5",
        class_id="C1",
        subject_id="ENG",
    )
    timetable = Timetable(
        timetable_id="soft_test",
        dataset_id=sample_dataset.dataset_id,
        scheduled_sessions=[s1, s2],
    )

    report = validate(timetable, sample_dataset)

    assert "SC-001" in report.soft_penalties
    assert "SC-002" in report.soft_penalties
    assert "SC-003" in report.soft_penalties
    assert "SC-004" in report.soft_penalties
    assert "SC-005" in report.soft_penalties
    # Idle gap at period 2 should produce SC-001 penalty = 1.0 * weight (1.0) = 1.0
    assert report.soft_penalties["SC-001"] >= 1.0
