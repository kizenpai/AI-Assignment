"""Unit tests for MRV and Degree variable ordering heuristics.

Tests TRD TC-H2-1, TC-H3-1, and ASM-T006.
"""

import pytest

from src.algorithms.heuristics import (
    calculate_variable_degree,
    select_unassigned_variable,
)
from src.csp.domains import SlotValue
from src.csp.variables import SessionVariable


def test_tc_h2_1_mrv_selection():
    """TRD TC-H2-1: Two unassigned variables where one has 2 legal values and the other has 5.

    MRV MUST select the 2-value variable next.
    """
    v1 = SessionVariable(requirement_id="REQ-V1", class_id="C1", subject_id="MATH", teacher_id="T1")
    v2 = SessionVariable(requirement_id="REQ-V2", class_id="C2", subject_id="ENG", teacher_id="T2")

    dummy_slot = SlotValue(day=0, start_period=1, room_id="R1")
    domains = {
        "REQ-V1": [dummy_slot] * 5,  # 5 remaining values
        "REQ-V2": [dummy_slot] * 2,  # 2 remaining values
    }

    selected = select_unassigned_variable(
        unassigned_vars=[v1, v2],
        domains=domains,
        use_mrv=True,
        use_degree=True,
    )

    assert selected.requirement_id == "REQ-V2"


def test_tc_h3_1_degree_heuristic_tie_break():
    """TRD TC-H3-1: Two MRV-tied variables.

    v1 shares a teacher with 3 other unassigned variables.
    v2 shares a teacher with 1 other unassigned variable.
    Degree Heuristic MUST select v1.
    """
    v1 = SessionVariable(requirement_id="REQ-V1", class_id="C1", subject_id="MATH", teacher_id="T_BUSY")
    v2 = SessionVariable(requirement_id="REQ-V2", class_id="C2", subject_id="ENG", teacher_id="T_CALM")

    # 3 other variables sharing teacher T_BUSY with v1
    v3 = SessionVariable(requirement_id="REQ-V3", class_id="C3", subject_id="MATH", teacher_id="T_BUSY")
    v4 = SessionVariable(requirement_id="REQ-V4", class_id="C4", subject_id="MATH", teacher_id="T_BUSY")
    v5 = SessionVariable(requirement_id="REQ-V5", class_id="C5", subject_id="MATH", teacher_id="T_BUSY")

    # 1 other variable sharing teacher T_CALM with v2
    v6 = SessionVariable(requirement_id="REQ-V6", class_id="C6", subject_id="ENG", teacher_id="T_CALM")

    unassigned = [v1, v2, v3, v4, v5, v6]

    dummy_slot = SlotValue(day=0, start_period=1, room_id="R1")
    # All variables have identical domain size of 3 (MRV tie)
    domains = {v.requirement_id: [dummy_slot] * 3 for v in unassigned}

    # Degree for v1 should be 3 (v3, v4, v5 share teacher)
    assert calculate_variable_degree(v1, unassigned) == 3
    # Degree for v2 should be 1 (v6 shares teacher)
    assert calculate_variable_degree(v2, unassigned) == 1

    # When choosing between v1 and v2, Degree Heuristic MUST select v1
    selected = select_unassigned_variable(
        unassigned_vars=[v1, v2],
        domains=domains,
        use_mrv=True,
        use_degree=True,
    )

    assert selected.requirement_id == "REQ-V1"


def test_deterministic_lexicographic_tie_break():
    """ASM-T006: When MRV and Degree are tied, break ties deterministically by requirement_id."""
    v_b = SessionVariable(requirement_id="REQ-B", class_id="C1", subject_id="MATH", teacher_id="T1")
    v_a = SessionVariable(requirement_id="REQ-A", class_id="C2", subject_id="ENG", teacher_id="T2")

    dummy_slot = SlotValue(day=0, start_period=1, room_id="R1")
    domains = {
        "REQ-A": [dummy_slot] * 4,
        "REQ-B": [dummy_slot] * 4,
    }

    # Pass in [v_b, v_a] order
    selected = select_unassigned_variable(
        unassigned_vars=[v_b, v_a],
        domains=domains,
        use_mrv=True,
        use_degree=True,
    )

    assert selected.requirement_id == "REQ-A"
