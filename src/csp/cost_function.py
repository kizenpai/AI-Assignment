"""Cost / objective function for local search algorithms (TRD G.6).

Combines hard constraint violation counts and soft constraint penalties:
total_cost = WEIGHT_HARD * hard_violations + soft_penalty

CRITICAL ARCHITECTURAL PRINCIPLE (DD-015):
The weighted cost is used ONLY internally by local search algorithms (Min-Conflicts,
Simulated Annealing, Hybrid) to guide exploration. The weighted cost is NEVER the
authority on validity. Only src/csp/validator.py (independent unweighted check)
determines whether status is "Valid".
"""

from __future__ import annotations

from typing import Dict, Optional

from src.csp.constraints import ALL_HARD_CONSTRAINTS
from src.csp.models import Dataset, Timetable
from src.csp.soft_constraints import evaluate_soft_penalties


# Tunable constant (ASM-T004): set sufficiently large so that feasible states
# are always preferred over hard-violating states during local search.
WEIGHT_HARD: float = 1000.0


def calculate_hard_violation_count(timetable: Timetable, dataset: Dataset) -> int:
    """Count the total number of hard constraint violations across all registered evaluators."""
    total = 0
    for constraint in ALL_HARD_CONSTRAINTS:
        violations = constraint.evaluate(timetable, dataset)
        total += len(violations)
    return total


def total_cost(
    timetable: Timetable,
    dataset: Dataset,
    soft_weights: Optional[Dict[str, float]] = None,
    weight_hard: float = WEIGHT_HARD,
) -> float:
    """Calculate the aggregate weighted cost function (TRD G.6 & DD-014).

    total_cost = WEIGHT_HARD * hard_violations + soft_penalty
    """
    hard_count = calculate_hard_violation_count(timetable, dataset)
    soft_total, _ = evaluate_soft_penalties(timetable, dataset, weights=soft_weights)

    return (weight_hard * hard_count) + soft_total
