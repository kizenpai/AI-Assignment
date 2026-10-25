"""Forward Checking domain filtering for Backtracking CSP search.

Implements TRD Section H.4 and TC-H4-1:
- Prunes inconsistent values from the domains of unassigned neighbor variables after an assignment.
- Detects domain wipeouts early to trigger immediate backtracking before deeper recursion.
- Maintains undo records to restore pruned values on backtrack.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from src.csp.domains import SlotValue
from src.csp.models import Dataset
from src.csp.variables import SessionVariable


def forward_check(
    assigned_var: SessionVariable,
    assigned_val: SlotValue,
    unassigned_vars: List[SessionVariable],
    domains: Dict[str, List[SlotValue]],
    current_assignment: Dict[str, SlotValue],
    var_map: Dict[str, SessionVariable],
    dataset: Dataset,
) -> Tuple[bool, Dict[str, List[SlotValue]]]:
    """Prune inconsistent values from neighbor unassigned variables after tentative assignment.

    Checks:
    - Same teacher overlap (HC-001)
    - Same class overlap (HC-002)
    - Same room overlap (HC-003)
    - Teacher daily / weekly workload bounds (HC-008)

    Args:
        assigned_var: The variable just assigned.
        assigned_val: The value assigned to it.
        unassigned_vars: List of variables not yet assigned.
        domains: Current mutable domain dictionary.
        current_assignment: Current partial assignment dictionary (including assigned_var).
        var_map: Lookup dictionary of all SessionVariables by requirement_id.
        dataset: The dataset.

    Returns:
        (no_wipeout, pruned_map) where no_wipeout is False if any domain became empty,
        and pruned_map records the values removed from each variable.
    """
    pruned: Dict[str, List[SlotValue]] = {}

    teacher = dataset.get_teacher(assigned_var.teacher_id)
    t_daily_max = teacher.max_daily_periods if teacher else None
    t_weekly_max = teacher.max_weekly_periods if teacher else None

    # Calculate teacher current committed workload
    teacher_daily_committed = 0
    teacher_weekly_committed = 0
    if t_daily_max is not None or t_weekly_max is not None:
        for aid, aval in current_assignment.items():
            if var_map[aid].teacher_id == assigned_var.teacher_id:
                if aval.day == assigned_val.day:
                    teacher_daily_committed += aval.duration_periods
                teacher_weekly_committed += aval.duration_periods

    for other_var in unassigned_vars:
        other_id = other_var.requirement_id
        current_vals = domains.get(other_id, [])
        if not current_vals:
            continue

        shares_teacher = (other_var.teacher_id == assigned_var.teacher_id)
        shares_class = (other_var.class_id == assigned_var.class_id)

        surviving: List[SlotValue] = []
        removed: List[SlotValue] = []

        for v in current_vals:
            # 1. Overlap with assigned_val
            overlaps_time = assigned_val.overlaps_in_time(v)

            if shares_teacher and overlaps_time:
                removed.append(v)
                continue

            if shares_class and overlaps_time:
                removed.append(v)
                continue

            if v.room_id == assigned_val.room_id and overlaps_time:
                removed.append(v)
                continue

            # 2. Workload capacity check for same teacher
            if shares_teacher:
                if t_daily_max is not None and v.day == assigned_val.day:
                    if teacher_daily_committed + v.duration_periods > t_daily_max:
                        removed.append(v)
                        continue
                if t_weekly_max is not None:
                    if teacher_weekly_committed + v.duration_periods > t_weekly_max:
                        removed.append(v)
                        continue

            surviving.append(v)

        if removed:
            pruned[other_id] = removed
            domains[other_id] = surviving

            # Domain wipeout check (TC-H4-1)
            if len(surviving) == 0:
                return False, pruned

    return True, pruned


def restore_domains(
    domains: Dict[str, List[SlotValue]],
    pruned_map: Dict[str, List[SlotValue]],
) -> None:
    """Restore pruned values to domains when backtracking."""
    for var_id, removed_vals in pruned_map.items():
        if var_id in domains:
            domains[var_id].extend(removed_vals)
