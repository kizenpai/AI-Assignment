"""Algorithms package: Backtracking, Min-Conflicts, Heuristics, Forward Checking, and base contracts."""

from src.algorithms.backtracking import solve_backtracking
from src.algorithms.base import AlgorithmConfig, AlgorithmResult, TerminationStatus
from src.algorithms.forward_checking import forward_check, restore_domains
from src.algorithms.heuristics import (
    calculate_variable_degree,
    order_domain_values,
    select_unassigned_variable,
)
from src.algorithms.min_conflicts import count_var_conflicts, solve_min_conflicts

__all__ = [
    "AlgorithmConfig",
    "AlgorithmResult",
    "TerminationStatus",
    "solve_backtracking",
    "solve_min_conflicts",
    "count_var_conflicts",
    "select_unassigned_variable",
    "calculate_variable_degree",
    "order_domain_values",
    "forward_check",
    "restore_domains",
]
