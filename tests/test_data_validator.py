"""Unit tests for dataset loading, structural validation, and requirement expansion.

Tests TRD TC-DV-1 and PRD FR-001..FR-005.
"""

from pathlib import Path
import pytest

from src.services.data_loader import (
    DatasetParseError,
    expand_requirements,
    load_dataset_from_dict,
    load_dataset_from_file,
    load_dataset_from_json,
)
from src.services.data_validator import (
    DatasetValidationException,
    validate_dataset_dict,
)
from src.csp.models import RequirementInput


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def test_small_dataset_loads_and_is_valid():
    """Verify data/small_dataset.json loads cleanly and passes all validation checks."""
    path = DATA_DIR / "small_dataset.json"
    dataset, report = load_dataset_from_file(path)

    assert report.is_valid is True
    assert len(report.errors) == 0
    assert dataset.dataset_id == "small_v1"
    assert len(dataset.classes) == 3
    assert len(dataset.teachers) == 6
    assert len(dataset.rooms) == 4
    assert len(dataset.subjects) == 6
    assert len(dataset.requirements) == 18
    # Total required sessions after expansion:
    # Each class has 3+3+3+2+2 single sessions = 13 + 1 lab block (duration 2) = 14 RequiredSessions
    # Across 3 classes: 14 * 3 = 42 RequiredSessions
    assert len(dataset.required_sessions) == 42


def test_large_dataset_loads_and_is_valid():
    """Verify data/large_dataset.json satisfies PRD M.3 (8 classes, 15 teachers, 8 rooms)."""
    path = DATA_DIR / "large_dataset.json"
    dataset, report = load_dataset_from_file(path)

    assert report.is_valid is True
    assert len(report.errors) == 0
    assert len(dataset.classes) >= 8
    assert len(dataset.teachers) >= 15
    assert len(dataset.rooms) >= 8
    assert dataset.periods_per_day == 7


def test_infeasible_sample_is_structurally_valid():
    """Verify data/infeasible_sample.json is structurally valid (FR-005), but mathematically constrained."""
    path = DATA_DIR / "infeasible_sample.json"
    dataset, report = load_dataset_from_file(path)

    assert report.is_valid is True
    assert len(report.errors) == 0
    assert len(dataset.classes) == 2
    assert len(dataset.teachers) == 1
    # T1 only available in 1 slot (29 slots unavailable out of 30)
    assert len(dataset.teachers[0].unavailable_slots) == 29
    assert len(dataset.required_sessions) == 2


def test_tc_dv_1_missing_teacher_reference():
    """TRD TC-DV-1: dataset references a teacher_id not present in teachers list.

    Expected: Reports a blocking error identifying the missing reference (FR-005).
    """
    path = DATA_DIR / "small_dataset.json"
    dataset, _ = load_dataset_from_file(path)
    raw = dataset.to_dict()

    # Tamper with the first requirement to reference a non-existent teacher
    raw["requirements"][0]["teacher_id"] = "T_NON_EXISTENT"

    report = validate_dataset_dict(raw)
    assert report.is_valid is False
    assert any(
        e.code == "VAL_UNKNOWN_TEACHER_REF" and "T_NON_EXISTENT" in e.message
        for e in report.errors
    )


def test_missing_class_reference():
    """Requirement references unknown class_id -> blocking error."""
    path = DATA_DIR / "small_dataset.json"
    dataset, _ = load_dataset_from_file(path)
    raw = dataset.to_dict()
    raw["requirements"][0]["class_id"] = "C_UNKNOWN"

    report = validate_dataset_dict(raw)
    assert report.is_valid is False
    assert any(
        e.code == "VAL_UNKNOWN_CLASS_REF" and "C_UNKNOWN" in e.message
        for e in report.errors
    )


def test_missing_subject_reference():
    """Requirement references unknown subject_id -> blocking error."""
    path = DATA_DIR / "small_dataset.json"
    dataset, _ = load_dataset_from_file(path)
    raw = dataset.to_dict()
    raw["requirements"][0]["subject_id"] = "SUBJ_UNKNOWN"

    report = validate_dataset_dict(raw)
    assert report.is_valid is False
    assert any(
        e.code == "VAL_UNKNOWN_SUBJECT_REF" and "SUBJ_UNKNOWN" in e.message
        for e in report.errors
    )


def test_duplicate_class_id():
    """Duplicate class_id -> blocking error."""
    path = DATA_DIR / "small_dataset.json"
    dataset, _ = load_dataset_from_file(path)
    raw = dataset.to_dict()
    raw["classes"].append({"class_id": "C1", "name": "Duplicate C1", "size": 30})

    report = validate_dataset_dict(raw)
    assert report.is_valid is False
    assert any(e.code == "VAL_DUPLICATE_CLASS_ID" and e.entity_id == "C1" for e in report.errors)


def test_duplicate_teacher_id():
    """Duplicate teacher_id -> blocking error."""
    path = DATA_DIR / "small_dataset.json"
    dataset, _ = load_dataset_from_file(path)
    raw = dataset.to_dict()
    raw["teachers"].append({"teacher_id": "T1", "name": "Duplicate T1", "subjects_qualified": ["MATH"]})

    report = validate_dataset_dict(raw)
    assert report.is_valid is False
    assert any(e.code == "VAL_DUPLICATE_TEACHER_ID" and e.entity_id == "T1" for e in report.errors)


def test_teacher_unqualified_for_subject():
    """Teacher assigned to teach a subject not in subjects_qualified -> blocking error."""
    path = DATA_DIR / "small_dataset.json"
    dataset, _ = load_dataset_from_file(path)
    raw = dataset.to_dict()
    # T1 is only qualified for MATH, assign T1 to teach ENG
    raw["requirements"][0]["subject_id"] = "ENG"
    raw["requirements"][0]["teacher_id"] = "T1"

    report = validate_dataset_dict(raw)
    assert report.is_valid is False
    assert any(e.code == "VAL_TEACHER_NOT_QUALIFIED" for e in report.errors)


def test_slot_day_out_of_bounds():
    """Slot day out of bounds -> blocking error."""
    path = DATA_DIR / "small_dataset.json"
    dataset, _ = load_dataset_from_file(path)
    raw = dataset.to_dict()
    # Days is 5 (0..4), set unavailable slot to day 5
    raw["teachers"][0]["unavailable_slots"].append({"day": 5, "period": 1})

    report = validate_dataset_dict(raw)
    assert report.is_valid is False
    assert any(e.code == "VAL_SLOT_DAY_OUT_OF_BOUNDS" for e in report.errors)


def test_slot_period_out_of_bounds():
    """Slot period out of bounds -> blocking error."""
    path = DATA_DIR / "small_dataset.json"
    dataset, _ = load_dataset_from_file(path)
    raw = dataset.to_dict()
    # periods_per_day is 6, set unavailable slot to period 7
    raw["teachers"][0]["unavailable_slots"].append({"day": 0, "period": 7})

    report = validate_dataset_dict(raw)
    assert report.is_valid is False
    assert any(e.code == "VAL_SLOT_PERIOD_OUT_OF_BOUNDS" for e in report.errors)


def test_no_compatible_room_for_class_size():
    """When a class is larger than all rooms -> blocking error."""
    path = DATA_DIR / "small_dataset.json"
    dataset, _ = load_dataset_from_file(path)
    raw = dataset.to_dict()
    # Make C1 size 100, while max room capacity is 40
    raw["classes"][0]["size"] = 100

    report = validate_dataset_dict(raw)
    assert report.is_valid is False
    assert any(e.code == "VAL_NO_COMPATIBLE_ROOM" for e in report.errors)


def test_class_weekly_hours_overload():
    """When a class requires more hours than the entire week has -> blocking error."""
    path = DATA_DIR / "small_dataset.json"
    dataset, _ = load_dataset_from_file(path)
    raw = dataset.to_dict()
    # Total available slots per class = 5 * 6 = 30
    # Add a requirement for 40 hours for C1
    raw["requirements"][0]["weekly_periods"] = 40

    report = validate_dataset_dict(raw)
    assert report.is_valid is False
    assert any(e.code == "VAL_CLASS_OVERLOAD" for e in report.errors)


def test_malformed_json_raises_parse_error():
    """Malformed JSON string -> raises DatasetParseError."""
    with pytest.raises(DatasetParseError):
        load_dataset_from_json("{ malformed: json, }")


def test_strict_mode_raises_validation_exception():
    """In strict mode, blocking validation errors raise DatasetValidationException."""
    invalid_data = {"dataset_id": "broken"}
    with pytest.raises(DatasetValidationException):
        load_dataset_from_dict(invalid_data, strict=True)


def test_dd008_requirement_expansion():
    """Verify DD-008 requirement expansion logic."""
    reqs = [
        RequirementInput(
            class_id="C1",
            subject_id="MATH",
            teacher_id="T1",
            weekly_periods=4,
            duration_periods=1,
            consecutive_required=False,
        ),
        RequirementInput(
            class_id="C1",
            subject_id="CHEM_LAB",
            teacher_id="T3",
            weekly_periods=2,
            duration_periods=2,
            consecutive_required=True,
        ),
    ]

    sessions = expand_requirements(reqs)

    # MATH expands into 4 sessions
    math_sessions = [s for s in sessions if s.subject_id == "MATH"]
    assert len(math_sessions) == 4
    for i, s in enumerate(math_sessions, 1):
        assert s.requirement_id == f"REQ-C1-MATH-{i:02d}"
        assert s.duration_periods == 1
        assert s.occurrence_index == i
        assert s.occurrence_total == 4
        assert s.consecutive_required is False

    # CHEM_LAB expands into 1 session of duration 2
    lab_sessions = [s for s in sessions if s.subject_id == "CHEM_LAB"]
    assert len(lab_sessions) == 1
    assert lab_sessions[0].requirement_id == "REQ-C1-CHEM_LAB-01"
    assert lab_sessions[0].duration_periods == 2
    assert lab_sessions[0].occurrence_index == 1
    assert lab_sessions[0].occurrence_total == 1
    assert lab_sessions[0].consecutive_required is True
