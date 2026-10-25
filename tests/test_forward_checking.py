"""Unit tests for Forward Checking domain pruning and wipeout detection.

Tests TRD TC-H4-1 and Section H.4.
"""

import pytest

from src.algorithms.backtracking import solve_backtracking
from src.algorithms.base import AlgorithmConfig
from src.algorithms.forward_checking import forward_check, restore_domains
from src.csp.domains import SlotValue
from src.csp.models import Class, Dataset, RequirementInput, Room, SlotRef, Subject, Teacher
from src.csp.variables import SessionVariable
from src.services.data_loader import expand_requirements


def test_tc_h4_1_wipeout_detected_before_deeper_recursion():
    """TRD TC-H4-1: Construct a 3-variable fixture where assigning the first variable

    empties the domain of a second; FC MUST detect the wipeout before recursing into the third variable.
    """
    # 2 classes (C1, C2), 1 teacher (T1), only 1 slot (Day 0, Period 1) available for T1.
    # Class C3 requires teacher T2 (completely independent).
    dataset = Dataset(
        dataset_id="test_fc_wipeout",
        description="Fixture for TC-H4-1",
        days=1,
        periods_per_day=2,
        lunch_period=None,
        classes=[
            Class(class_id="C1", name="C1", size=20),
            Class(class_id="C2", name="C2", size=20),
            Class(class_id="C3", name="C3", size=20),
        ],
        teachers=[
            Teacher(
                teacher_id="T1",
                name="T1",
                subjects_qualified=["MATH"],
                unavailable_slots=[SlotRef(day=0, period=2)],  # T1 only available on (0, 1)
            ),
            Teacher(
                teacher_id="T2",
                name="T2",
                subjects_qualified=["ENG"],
            ),
        ],
        subjects=[
            Subject(subject_id="MATH", name="Math"),
            Subject(subject_id="ENG", name="English"),
        ],
        rooms=[
            Room(room_id="R1", capacity=30, room_type="lecture"),
            Room(room_id="R2", capacity=30, room_type="lecture"),
        ],
        requirements=[
            RequirementInput(class_id="C1", subject_id="MATH", teacher_id="T1", weekly_periods=1),
            RequirementInput(class_id="C2", subject_id="MATH", teacher_id="T1", weekly_periods=1),
            RequirementInput(class_id="C3", subject_id="ENG", teacher_id="T2", weekly_periods=1),
        ],
    )
    dataset.required_sessions = expand_requirements(dataset.requirements)

    config = AlgorithmConfig(
        algorithm="backtracking",
        use_forward_checking=True,
        max_search_nodes=100,
    )

    result = solve_backtracking(dataset, config)

    # Infeasible: C1 and C2 both compete for T1's only slot (Day 0, Period 1)
    assert result.termination == "exhausted"
    # Forward checking detects the wipeout on C2 immediately when C1 is placed,
    # before ever branching on C3!
    assert result.extra_metrics["wipeouts_detected"] >= 1
    # Search should terminate in very few nodes (e.g. <= 5 nodes)
    assert result.search_nodes_or_iterations <= 6


def test_forward_check_and_restore():
    """Verify forward_check removes conflicting slots and restore_domains restores them."""
    dataset = Dataset(
        dataset_id="test_fc_restore",
        description="Verify forward check and restore",
        days=1,
        periods_per_day=3,
        classes=[Class(class_id="C1", name="C1", size=20), Class(class_id="C2", name="C2", size=20)],
        teachers=[Teacher(teacher_id="T1", name="T1", subjects_qualified=["MATH"])],
        subjects=[Subject(subject_id="MATH", name="Math")],
        rooms=[Room(room_id="R1", capacity=30), Room(room_id="R2", capacity=30)],
        requirements=[],
    )

    v1 = SessionVariable(requirement_id="REQ-1", class_id="C1", subject_id="MATH", teacher_id="T1")
    v2 = SessionVariable(requirement_id="REQ-2", class_id="C2", subject_id="MATH", teacher_id="T1")

    var_map = {"REQ-1": v1, "REQ-2": v2}

    slot_a = SlotValue(day=0, start_period=1, room_id="R1")
    slot_b = SlotValue(day=0, start_period=2, room_id="R1")

    domains = {
        "REQ-2": [slot_a, slot_b]
    }

    # Tentatively assign v1 to slot_a
    current_assignment = {"REQ-1": slot_a}
    no_wipeout, pruned = forward_check(
        assigned_var=v1,
        assigned_val=slot_a,
        unassigned_vars=[v2],
        domains=domains,
        current_assignment=current_assignment,
        var_map=var_map,
        dataset=dataset,
    )

    assert no_wipeout is True
    # slot_a should have been pruned from v2 because both share teacher T1
    assert slot_a in pruned["REQ-2"]
    assert domains["REQ-2"] == [slot_b]

    # Now restore domains on backtrack
    restore_domains(domains, pruned)
    assert set(domains["REQ-2"]) == {slot_a, slot_b}
