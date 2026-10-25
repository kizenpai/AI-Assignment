"""Variable and value ordering heuristics for Backtracking CSP search.

Implements TRD Section H.2, H.3, and ASM-T005/ASM-T006:
- Minimum Remaining Values (MRV): Pick unassigned variable with smallest domain.
- Degree Heuristic (DH): Break MRV ties by picking variable with most constraints on other unassigned variables.
- Deterministic lexicographic tie-breaking (ASM-T006).
- Least Constraining / Soft-Preference Value Ordering (ASM-T005).
"""

from __future__ import annotations

from typing import Dict, List, Optional

from src.csp.domains import SlotValue
from src.csp.models import Dataset
from src.csp.variables import SessionVariable


def calculate_variable_degree(
    var: SessionVariable,
    unassigned_vars: List[SessionVariable],
) -> int:
    """Calculate the degree of a variable among currently unassigned variables.

    Degree is the number of other unassigned variables that share a hard constraint
    with this variable (same teacher or same class group).
    """
    degree = 0
    for other in unassigned_vars:
        if other.requirement_id != var.requirement_id:
            if other.teacher_id == var.teacher_id or other.class_id == var.class_id:
                degree += 1
    return degree


def select_unassigned_variable(
    unassigned_vars: List[SessionVariable],
    domains: Dict[str, List[SlotValue]],
    use_mrv: bool = True,
    use_degree: bool = True,
) -> SessionVariable:
    """Select the next variable to assign in Backtracking search.

    Ordering policy:
    1. If use_mrv: Primary criterion is Minimum Remaining Values (smallest domain size).
    2. If use_degree: Tie-breaker is Degree Heuristic (largest degree among unassigned).
    3. Final tie-breaker: Lexicographic requirement_id order (ASM-T006 for determinism).
    """
    if not unassigned_vars:
        raise ValueError("Cannot select variable from an empty unassigned list.")

    if not use_mrv and not use_degree:
        # Plain static order: first unassigned variable (sorted by requirement_id for determinism)
        return min(unassigned_vars, key=lambda v: v.requirement_id)

    def sort_key(v: SessionVariable) -> tuple:
        # MRV component: remaining legal values (lower is better)
        mrv_val = len(domains.get(v.requirement_id, [])) if use_mrv else 0

        # Degree component: number of constrained unassigned variables (higher is better, so negate)
        deg_val = -calculate_variable_degree(v, unassigned_vars) if use_degree else 0

        # Deterministic tie-breaker
        return (mrv_val, deg_val, v.requirement_id)

    return min(unassigned_vars, key=sort_key)


def order_domain_values(
    var: SessionVariable,
    domain_values: List[SlotValue],
    dataset: Dataset,
    current_assignment: Optional[Dict[str, SlotValue]] = None,
) -> List[SlotValue]:
    """Order candidate values for a variable (TRD H.1 & ASM-T005).

    Orders values by soft-preference penalty contribution (e.g. avoid undesired slots,
    prefer preferred slots) while maintaining deterministic slot ordering.
    """
    teacher = dataset.get_teacher(var.teacher_id)
    undesired_slots = {s.as_tuple() for s in teacher.undesired_slots} if teacher else set()
    preferred_slots = {s.as_tuple() for s in teacher.preferred_slots} if teacher else set()

    def value_cost(val: SlotValue) -> tuple:
        # Prefer preferred slots (-1), neutral (0), undesired (+1)
        pref_penalty = 0
        for p in val.periods:
            if (val.day, p) in undesired_slots:
                pref_penalty += 1
            elif (val.day, p) in preferred_slots:
                pref_penalty -= 1

        # Stable tie-breaker: day, start_period, room_id
        return (pref_penalty, val.day, val.start_period, val.room_id)

    return sorted(domain_values, key=value_cost)
