"""Unit tests for Min-Conflicts local search solver.

Tests TRD TC-MC-1, TC-MC-2, PRD FR-011, and DD-018/DD-020.
"""

from pathlib import Path
import pytest

from src.algorithms.base import AlgorithmConfig
from src.algorithms.min_conflicts import solve_min_conflicts
from src.csp.models import Class, Dataset, RequirementInput, Room, Subject, Teacher
from src.csp.validator import validate
from src.services.data_loader import expand_requirements, load_dataset_from_file


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture
def small_feasible_fixture():
    dataset = Dataset(
        dataset_id="test_mc_fixture",
        description="Feasible fixture for Min-Conflicts",
        days=3,
        periods_per_day=3,
        lunch_period=None,
        classes=[
            Class(class_id="C1", name="C1", size=25),
            Class(class_id="C2", name="C2", size=25),
        ],
        teachers=[
            Teacher(teacher_id="T1", name="T1", subjects_qualified=["MATH"]),
            Teacher(teacher_id="T2", name="T2", subjects_qualified=["ENG"]),
        ],
        subjects=[
            Subject(subject_id="MATH", name="Math"),
            Subject(subject_id="ENG", name="English"),
        ],
        rooms=[
            Room(room_id="R101", capacity=30, room_type="lecture"),
            Room(room_id="R102", capacity=30, room_type="lecture"),
        ],
        requirements=[
            RequirementInput(class_id="C1", subject_id="MATH", teacher_id="T1", weekly_periods=2),
            RequirementInput(class_id="C1", subject_id="ENG", teacher_id="T2", weekly_periods=2),
            RequirementInput(class_id="C2", subject_id="MATH", teacher_id="T1", weekly_periods=2),
            RequirementInput(class_id="C2", subject_id="ENG", teacher_id="T2", weekly_periods=2),
        ],
    )
    dataset.required_sessions = expand_requirements(dataset.requirements)
    return dataset


def test_tc_mc_1_feasible_convergence(small_feasible_fixture):
    """TRD TC-MC-1: Feasible fixture, fixed seed.

    Expected: Converges to zero hard conflicts within max_iterations, termination='success', status='Valid'.
    """
    config = AlgorithmConfig(
        algorithm="min_conflicts",
        max_iterations=2000,
        random_seed=42,
    )

    result = solve_min_conflicts(small_feasible_fixture, config)

    assert result.termination == "success"
    assert result.status == "Valid"
    assert result.timetable is not None
    assert result.extra_metrics["best_hard_conflicts"] == 0

    # Cross-check with independent validator (ASM-T013)
    val_report = validate(result.timetable, small_feasible_fixture)
    assert val_report.is_valid is True
    assert val_report.total_hard_violations == 0


def test_tc_mc_2_determinism_with_fixed_seed(small_feasible_fixture):
    """TRD TC-MC-2: Same fixture, same seed, run twice -> identical result (reproducibility check)."""
    config = AlgorithmConfig(
        algorithm="min_conflicts",
        max_iterations=1000,
        random_seed=123,
    )

    run1 = solve_min_conflicts(small_feasible_fixture, config)
    run2 = solve_min_conflicts(small_feasible_fixture, config)

    assert run1.termination == run2.termination
    assert run1.status == run2.status
    assert run1.search_nodes_or_iterations == run2.search_nodes_or_iterations

    # Compare exact session assignments
    sessions1 = [
        (s.requirement_id, s.day, s.start_period, s.room_id)
        for s in run1.timetable.scheduled_sessions
    ]
    sessions2 = [
        (s.requirement_id, s.day, s.start_period, s.room_id)
        for s in run2.timetable.scheduled_sessions
    ]
    assert sessions1 == sessions2


def test_min_conflicts_on_infeasible_sample():
    """Verify Min-Conflicts on infeasible_sample.json reaches search_limit and reports Invalid (DD-018).

    It must never silently upgrade an unresolved candidate to Valid.
    """
    path = DATA_DIR / "infeasible_sample.json"
    dataset, _ = load_dataset_from_file(path)

    config = AlgorithmConfig(
        algorithm="min_conflicts",
        max_iterations=200,
        random_seed=42,
    )

    result = solve_min_conflicts(dataset, config)

    assert result.termination == "search_limit"
    assert result.status == "Invalid"
    assert result.is_success is False


def test_min_conflicts_on_small_dataset():
    """Verify Min-Conflicts can find a valid timetable on data/small_dataset.json."""
    path = DATA_DIR / "small_dataset.json"
    dataset, _ = load_dataset_from_file(path)

    config = AlgorithmConfig(
        algorithm="min_conflicts",
        max_iterations=3000,
        random_seed=99,
    )

    result = solve_min_conflicts(dataset, config)

    assert result.termination == "success"
    assert result.status == "Valid"
    assert result.timetable is not None
    assert len(result.timetable.scheduled_sessions) == len(dataset.required_sessions)
