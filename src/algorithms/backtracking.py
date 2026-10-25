"""Backtracking CSP solver with MRV, Degree Heuristic, and Forward Checking.

Implements TRD Section H.1 - H.4, PRD FR-008, FR-009, FR-010, NFR-002, and NFR-004:
- Hand-rolled CSP search demonstrating academic concepts without opaque third-party libraries (DD-004).
- MRV variable selection with Degree Heuristic tie-breaking.
- Forward Checking for early dead-end detection and domain restoration.
- Distinct termination reporting: 'success', 'exhausted' (proof of infeasibility), 'search_limit'.
- Independent validation of candidate timetable per DD-018.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional
import uuid

from src.algorithms.base import AlgorithmConfig, AlgorithmResult
from src.algorithms.forward_checking import forward_check, restore_domains
from src.algorithms.heuristics import order_domain_values, select_unassigned_variable
from src.csp.constraints import is_assignment_consistent
from src.csp.domains import SlotValue, build_domains
from src.csp.models import Dataset, ScheduledSession, Timetable
from src.csp.validator import validate
from src.csp.variables import SessionVariable, build_variables


class _SearchStats:
    def __init__(self):
        self.nodes_expanded = 0
        self.backtracks = 0
        self.wipeouts_detected = 0
        self.hit_search_limit = False


def solve_backtracking(
    dataset: Dataset,
    config: Optional[AlgorithmConfig] = None,
) -> AlgorithmResult:
    """Solve the timetable scheduling problem using Backtracking CSP search.

    Args:
        dataset: The timetable dataset.
        config: Algorithm configuration (search limits, heuristics, forward checking flags).

    Returns:
        AlgorithmResult containing the candidate Timetable, termination status, and performance metrics.
    """
    if config is None:
        config = AlgorithmConfig(algorithm="backtracking")

    start_time = time.perf_counter()

    variables = build_variables(dataset)
    var_map: Dict[str, SessionVariable] = {v.requirement_id: v for v in variables}

    # Build initial domains with static constraints pre-filtered
    domains = build_domains(dataset, variables, strict=False)

    # Check if any variable has an initial empty domain
    empty_vars = [v.requirement_id for v in variables if not domains.get(v.requirement_id)]
    if empty_vars:
        elapsed = time.perf_counter() - start_time
        return AlgorithmResult(
            status="NoCandidate",
            termination="exhausted",
            timetable=None,
            runtime_seconds=elapsed,
            search_nodes_or_iterations=0,
            config_used=config,
            extra_metrics={"reason": f"Variables with empty initial domain: {empty_vars}"},
        )

    stats = _SearchStats()
    max_nodes = config.max_search_nodes or float("inf")

    # Stack-based or recursive backtracking
    assignment: Dict[str, SlotValue] = {}
    unassigned_vars = list(variables)

    def backtrack() -> Optional[Dict[str, SlotValue]]:
        stats.nodes_expanded += 1

        if stats.nodes_expanded >= max_nodes:
            stats.hit_search_limit = True
            return None

        # Base case: all variables assigned
        if not unassigned_vars:
            return assignment

        # Select next variable using MRV and Degree Heuristic
        var = select_unassigned_variable(
            unassigned_vars=unassigned_vars,
            domains=domains,
            use_mrv=config.use_mrv,
            use_degree=config.use_degree_heuristic,
        )

        unassigned_vars.remove(var)
        var_id = var.requirement_id

        # Order domain values using soft preferences
        candidate_values = order_domain_values(
            var=var,
            domain_values=domains.get(var_id, []),
            dataset=dataset,
            current_assignment=assignment,
        )

        for val in candidate_values:
            # Check pairwise consistency with current partial assignment
            if is_assignment_consistent(var, val, assignment, var_map, dataset):
                assignment[var_id] = val

                if config.use_forward_checking:
                    no_wipeout, pruned = forward_check(
                        assigned_var=var,
                        assigned_val=val,
                        unassigned_vars=unassigned_vars,
                        domains=domains,
                        current_assignment=assignment,
                        var_map=var_map,
                        dataset=dataset,
                    )

                    if no_wipeout:
                        result = backtrack()
                        if result is not None:
                            return result
                        if stats.hit_search_limit:
                            restore_domains(domains, pruned)
                            del assignment[var_id]
                            return None
                    else:
                        stats.wipeouts_detected += 1

                    # Backtrack: restore pruned domains
                    restore_domains(domains, pruned)
                else:
                    result = backtrack()
                    if result is not None:
                        return result
                    if stats.hit_search_limit:
                        del assignment[var_id]
                        return None

                del assignment[var_id]
                stats.backtracks += 1

        # Restore variable to unassigned list
        unassigned_vars.append(var)
        return None

    solution_assignment = backtrack()
    elapsed = time.perf_counter() - start_time

    # Determine termination cause and candidate timetable
    if solution_assignment is not None:
        # Success: convert assignment dictionary to Timetable
        scheduled_sessions: List[ScheduledSession] = []
        for req_id, val in solution_assignment.items():
            var = var_map[req_id]
            scheduled_sessions.append(
                ScheduledSession(
                    requirement_id=req_id,
                    day=val.day,
                    start_period=val.start_period,
                    duration_periods=val.duration_periods,
                    room_id=val.room_id,
                    teacher_id=var.teacher_id,
                    class_id=var.class_id,
                    subject_id=var.subject_id,
                )
            )

        timetable = Timetable(
            timetable_id=f"TT-BT-{uuid.uuid4().hex[:6].upper()}",
            dataset_id=dataset.dataset_id,
            scheduled_sessions=scheduled_sessions,
            unscheduled_requirement_ids=[],
            generated_by="Backtracking",
            status="NotEvaluated",
        )

        # Re-derive validity independently per DD-018
        report = validate(timetable, dataset, soft_weights=config.soft_weights)

        return AlgorithmResult(
            status=report.status,
            termination="success",
            timetable=timetable,
            runtime_seconds=elapsed,
            search_nodes_or_iterations=stats.nodes_expanded,
            config_used=config,
            extra_metrics={
                "nodes_expanded": stats.nodes_expanded,
                "backtracks": stats.backtracks,
                "wipeouts_detected": stats.wipeouts_detected,
                "validation_report": report.to_dict(),
            },
        )

    elif stats.hit_search_limit:
        # Search limit reached (NFR-002, distinct from proof of infeasibility)
        partial_sessions: List[ScheduledSession] = []
        for req_id, val in assignment.items():
            var = var_map[req_id]
            partial_sessions.append(
                ScheduledSession(
                    requirement_id=req_id,
                    day=val.day,
                    start_period=val.start_period,
                    duration_periods=val.duration_periods,
                    room_id=val.room_id,
                    teacher_id=var.teacher_id,
                    class_id=var.class_id,
                    subject_id=var.subject_id,
                )
            )

        unscheduled = [v.requirement_id for v in variables if v.requirement_id not in assignment]
        partial_tt = Timetable(
            timetable_id=f"TT-PARTIAL-{uuid.uuid4().hex[:6].upper()}",
            dataset_id=dataset.dataset_id,
            scheduled_sessions=partial_sessions,
            unscheduled_requirement_ids=unscheduled,
            generated_by="Backtracking",
            status="Incomplete",
        )

        report = validate(partial_tt, dataset, soft_weights=config.soft_weights)

        return AlgorithmResult(
            status=report.status,
            termination="search_limit",
            timetable=partial_tt,
            runtime_seconds=elapsed,
            search_nodes_or_iterations=stats.nodes_expanded,
            config_used=config,
            extra_metrics={
                "nodes_expanded": stats.nodes_expanded,
                "backtracks": stats.backtracks,
                "wipeouts_detected": stats.wipeouts_detected,
                "hit_limit": True,
            },
        )

    else:
        # Search tree fully exhausted without a solution -> Proof of Infeasibility
        return AlgorithmResult(
            status="NoCandidate",
            termination="exhausted",
            timetable=None,
            runtime_seconds=elapsed,
            search_nodes_or_iterations=stats.nodes_expanded,
            config_used=config,
            extra_metrics={
                "nodes_expanded": stats.nodes_expanded,
                "backtracks": stats.backtracks,
                "wipeouts_detected": stats.wipeouts_detected,
                "infeasibility_proven": True,
            },
        )
