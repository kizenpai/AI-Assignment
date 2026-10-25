"""Unit tests for CSP domain generation and static constraint filtering.

Tests TRD TC-DOM-1 and Section G.2.
"""

from pathlib import Path
import pytest

from src.csp.domains import DomainWipeoutAtBuildError, SlotValue, build_domains
from src.csp.models import Class, Dataset, RequirementInput, Room, Subject, Teacher
from src.csp.variables import build_variables
from src.services.data_loader import load_dataset_from_file


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def test_tc_dom_1_lab_duration_boundary():
    """TRD TC-DOM-1: A 2-period lab session on a day with periods 1..6 cannot start at period 6.

    Period 6 only has 1 trailing period left before the day ends, so period 6 must be excluded.
    """
    dataset = Dataset(
        dataset_id="test_dom_1",
        description="Testing block duration boundaries",
        days=5,
        periods_per_day=6,
        lunch_period=None,
        classes=[Class(class_id="C1", name="C1", size=20)],
        teachers=[Teacher(teacher_id="T1", name="T1", subjects_qualified=["LAB"])],
        subjects=[Subject(subject_id="LAB", name="Lab", requires_room_type="lab", is_lab=True)],
        rooms=[Room(room_id="R_LAB", capacity=30, room_type="lab")],
        requirements=[
            RequirementInput(
                class_id="C1",
                subject_id="LAB",
                teacher_id="T1",
                weekly_periods=2,
                duration_periods=2,
                consecutive_required=True,
            )
        ],
    )
    dataset.required_sessions = [
        dataset.requirements[0]
    ]  # expanded in data_loader normally; let's load or build variables
    from src.services.data_loader import expand_requirements
    dataset.required_sessions = expand_requirements(dataset.requirements)

    variables = build_variables(dataset)
    domains = build_domains(dataset, variables)

    var_id = variables[0].requirement_id
    domain_values = domains[var_id]

    # For 5 days, max start period is periods_per_day - duration + 1 = 6 - 2 + 1 = 5
    # So valid start periods are 1, 2, 3, 4, 5 (5 per day * 5 days = 25 values)
    assert len(domain_values) == 25
    assert all(val.start_period <= 5 for val in domain_values)
    assert not any(val.start_period == 6 for val in domain_values)


def test_domain_filtering_by_room_capacity_and_type():
    """Verify that domain filters out rooms with insufficient capacity or incompatible types (HC-004, HC-005)."""
    dataset = Dataset(
        dataset_id="test_filter",
        description="Testing room type & capacity filtering",
        days=1,
        periods_per_day=3,
        lunch_period=None,
        classes=[Class(class_id="C1", name="Large Class", size=40)],
        teachers=[Teacher(teacher_id="T1", name="T1", subjects_qualified=["CS"])],
        subjects=[Subject(subject_id="CS", name="CS", requires_room_type="computer_lab")],
        rooms=[
            Room(room_id="R_SMALL_LAB", capacity=25, room_type="computer_lab"),  # too small
            Room(room_id="R_LARGE_LEC", capacity=50, room_type="lecture"),       # wrong type
            Room(room_id="R_PERFECT", capacity=45, room_type="computer_lab"),    # matches!
        ],
        requirements=[
            RequirementInput(
                class_id="C1",
                subject_id="CS",
                teacher_id="T1",
                weekly_periods=1,
                duration_periods=1,
            )
        ],
    )
    from src.services.data_loader import expand_requirements
    dataset.required_sessions = expand_requirements(dataset.requirements)

    variables = build_variables(dataset)
    domains = build_domains(dataset, variables)

    var_id = variables[0].requirement_id
    domain_values = domains[var_id]

    # Only R_PERFECT should be in domain
    assert len(domain_values) == 3  # 3 periods on day 0
    assert all(val.room_id == "R_PERFECT" for val in domain_values)


def test_domain_filtering_by_lunch_and_teacher_availability():
    """Verify lunch period (HC-009) and teacher unavailable slots (HC-006) are pruned statically."""
    path = DATA_DIR / "small_dataset.json"
    dataset, _ = load_dataset_from_file(path)
    variables = build_variables(dataset)
    domains = build_domains(dataset, variables)

    # In small_dataset.json, lunch_period is 4. No domain slot should occupy period 4.
    for var in variables:
        dom = domains[var.requirement_id]
        for val in dom:
            assert 4 not in val.periods

    # In small_dataset.json, Teacher T1 is unavailable on Day 0, Period 1
    t1_vars = [v for v in variables if v.teacher_id == "T1"]
    for v in t1_vars:
        dom = domains[v.requirement_id]
        for val in dom:
            assert not (val.day == 0 and 1 in val.periods)


def test_domain_wipeout_raises_error_in_strict_mode():
    """Verify DomainWipeoutAtBuildError is raised when strict=True and no room matches."""
    dataset = Dataset(
        dataset_id="test_wipeout",
        description="Testing wipeout",
        days=1,
        periods_per_day=2,
        lunch_period=None,
        classes=[Class(class_id="C1", name="C1", size=100)],
        teachers=[Teacher(teacher_id="T1", name="T1", subjects_qualified=["MATH"])],
        subjects=[Subject(subject_id="MATH", name="Math")],
        rooms=[Room(room_id="R1", capacity=30, room_type="lecture")],  # cannot fit size 100
        requirements=[RequirementInput(class_id="C1", subject_id="MATH", teacher_id="T1", weekly_periods=1)],
    )
    from src.services.data_loader import expand_requirements
    dataset.required_sessions = expand_requirements(dataset.requirements)

    variables = build_variables(dataset)
    with pytest.raises(DomainWipeoutAtBuildError):
        build_domains(dataset, variables, strict=True)
