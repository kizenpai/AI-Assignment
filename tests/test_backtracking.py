"""Unit tests for Backtracking CSP solver.

Tests TRD TC-BT-1, TC-BT-2, TC-BT-3, PRD FR-008, NFR-002, and NFR-004.
"""

from pathlib import Path
import pytest

from src.algorithms.backtracking import solve_backtracking
from src.algorithms.base import AlgorithmConfig
from src.csp.models import Class, Dataset, RequirementInput, Room, Subject, Teacher
from src.services.data_loader import expand_requirements, load_dataset_from_file


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def test_tc_bt_1_feasible_small_fixture():
    """TRD TC-BT-1: Tiny 2-variable, obviously feasible fixture.

    Expected: Returns complete assignment, termination="success", status="Valid".
    """
    dataset = Dataset(
        dataset_id="test_bt_1",
        description="Feasible 2-variable fixture",
        days=2,
        periods_per_day=3,
        lunch_period=None,
        classes=[Class(class_id="C1", name="C1", size=20)],
        teachers=[
            Teacher(teacher_id="T1", name="T1", subjects_qualified=["MATH"]),
            Teacher(teacher_id="T2", name="T2", subjects_qualified=["ENG"]),
        ],
        subjects=[
            Subject(subject_id="MATH", name="Math"),
            Subject(subject_id="ENG", name="English"),
        ],
        rooms=[Room(room_id="R101", capacity=30, room_type="lecture")],
        requirements=[
            RequirementInput(class_id="C1", subject_id="MATH", teacher_id="T1", weekly_periods=1),
            RequirementInput(class_id="C1", subject_id="ENG", teacher_id="T2", weekly_periods=1),
        ],
    )
    dataset.required_sessions = expand_requirements(dataset.requirements)

    config = AlgorithmConfig(algorithm="backtracking", use_mrv=True, use_forward_checking=True)
    result = solve_backtracking(dataset, config)

    assert result.termination == "success"
    assert result.status == "Valid"
    assert result.is_success is True
    assert result.timetable is not None
    assert len(result.timetable.scheduled_sessions) == 2


def test_tc_bt_2_infeasible_sample_exhausts_search():
    """TRD TC-BT-2: Deliberately infeasible fixture (data/infeasible_sample.json).

    Expected: Exhausts search, termination="exhausted", status resolves to "NoCandidate".
    """
    path = DATA_DIR / "infeasible_sample.json"
    dataset, _ = load_dataset_from_file(path)

    config = AlgorithmConfig(algorithm="backtracking", max_search_nodes=5000)
    result = solve_backtracking(dataset, config)

    assert result.termination == "exhausted"
    assert result.status == "NoCandidate"
    assert result.timetable is None
    assert result.extra_metrics.get("infeasibility_proven") is True


def test_tc_bt_3_search_limit_distinct_from_exhausted():
    """TRD TC-BT-3: max_search_nodes=1 on a nontrivial fixture.

    Expected: termination="search_limit", distinct from "exhausted".
    """
    path = DATA_DIR / "small_dataset.json"
    dataset, _ = load_dataset_from_file(path)

    config = AlgorithmConfig(algorithm="backtracking", max_search_nodes=1)
    result = solve_backtracking(dataset, config)

    assert result.termination == "search_limit"
    assert result.termination != "exhausted"
    assert result.search_nodes_or_iterations >= 1


def test_solve_small_dataset_with_backtracking_and_heuristics():
    """Verify Backtracking + MRV + DH + FC finds a valid timetable on data/small_dataset.json."""
    path = DATA_DIR / "small_dataset.json"
    dataset, _ = load_dataset_from_file(path)

    config = AlgorithmConfig(
        algorithm="backtracking",
        use_mrv=True,
        use_degree_heuristic=True,
        use_forward_checking=True,
        max_search_nodes=200000,
    )

    result = solve_backtracking(dataset, config)

    assert result.termination == "success"
    assert result.status == "Valid"
    assert result.timetable is not None
    assert len(result.timetable.scheduled_sessions) == len(dataset.required_sessions)
    assert result.extra_metrics["validation_report"]["total_hard_violations"] == 0
