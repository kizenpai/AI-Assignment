"""Base data structures and output contracts for all scheduling algorithms.

Implements TRD Section H (Algorithm Design) and Common Algorithm Output Contract (PRD K.5):
- AlgorithmConfig: Unified configuration for all solvers.
- AlgorithmResult: Standardized output structure.
- TerminationStatus: Categorization of termination causes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional

from src.csp.models import Timetable, TimetableStatus


TerminationStatus = Literal[
    "success",          # Found a complete valid schedule
    "exhausted",        # Search space fully exhausted (proof of infeasibility for CSP)
    "search_limit",     # Hit node or iteration budget (not proof of infeasibility)
    "timeout",          # Hit wall-clock limit
    "internal_failure", # Unexpected exception or broken precondition
]


@dataclass
class AlgorithmConfig:
    """Unified configuration parameters for all scheduling algorithms."""

    algorithm: Literal["backtracking", "min_conflicts", "simulated_annealing", "hybrid"] = "backtracking"
    use_mrv: bool = True
    use_degree_heuristic: bool = True
    use_forward_checking: bool = True
    max_search_nodes: Optional[int] = 200000
    max_iterations: Optional[int] = 5000
    random_seed: Optional[int] = 42
    initial_temperature: float = 100.0
    cooling_rate: float = 0.95
    min_temperature: float = 0.01
    soft_weights: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "use_mrv": self.use_mrv,
            "use_degree_heuristic": self.use_degree_heuristic,
            "use_forward_checking": self.use_forward_checking,
            "max_search_nodes": self.max_search_nodes,
            "max_iterations": self.max_iterations,
            "random_seed": self.random_seed,
            "initial_temperature": self.initial_temperature,
            "cooling_rate": self.cooling_rate,
            "min_temperature": self.min_temperature,
            "soft_weights": dict(self.soft_weights) if self.soft_weights else None,
        }


@dataclass
class AlgorithmResult:
    """Standardized result returned by every scheduling algorithm (PRD K.5 & TRD H)."""

    status: TimetableStatus
    termination: TerminationStatus
    timetable: Optional[Timetable]
    runtime_seconds: float
    search_nodes_or_iterations: int
    config_used: AlgorithmConfig
    extra_metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.termination == "success" and self.status == "Valid"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "termination": self.termination,
            "is_success": self.is_success,
            "runtime_seconds": self.runtime_seconds,
            "search_nodes_or_iterations": self.search_nodes_or_iterations,
            "config_used": self.config_used.to_dict(),
            "extra_metrics": dict(self.extra_metrics),
            "timetable": self.timetable.to_dict() if self.timetable else None,
        }
