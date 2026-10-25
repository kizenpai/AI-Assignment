"""Timetable generator service.

Implements TRD Section C.2, B.4, and DD-018:
- Orchestrates CSP build -> algorithm invocation -> independent validation.
- Validates the dataset before scheduling starts.
- Sole interface through which the UI requests timetable generation.
"""

from __future__ import annotations

import logging
from typing import Optional

from src.algorithms.backtracking import solve_backtracking
from src.algorithms.base import AlgorithmConfig, AlgorithmResult
from src.csp.models import Dataset
from src.csp.validator import validate
from src.services.data_validator import validate_dataset_dict

logger = logging.getLogger("services.generator")


def generate(
    dataset: Dataset,
    config: Optional[AlgorithmConfig] = None,
) -> AlgorithmResult:
    """Orchestrate timetable generation for a dataset using the specified algorithm configuration.

    Flow (TRD B.4):
    1. Verify dataset has no blocking validation errors.
    2. Dispatch to the selected algorithm solver.
    3. Run independent validator (src/csp/validator.py) on any produced candidate (DD-018).
    4. Return standardized AlgorithmResult.
    """
    if config is None:
        config = AlgorithmConfig(algorithm="backtracking")

    # 1. Verify dataset validity before search
    raw_dict = dataset.to_dict()
    val_report = validate_dataset_dict(raw_dict)
    if not val_report.is_valid:
        logger.warning("Generation aborted: dataset has blocking validation errors.")
        return AlgorithmResult(
            status="Invalid",
            termination="internal_failure",
            timetable=None,
            runtime_seconds=0.0,
            search_nodes_or_iterations=0,
            config_used=config,
            extra_metrics={"blocking_errors": [e.to_dict() for e in val_report.errors]},
        )

    # 2. Dispatch to algorithm
    algo = config.algorithm.lower()
    if algo == "backtracking":
        result = solve_backtracking(dataset, config)
    elif algo == "min_conflicts":
        from src.algorithms.min_conflicts import solve_min_conflicts
        result = solve_min_conflicts(dataset, config)
    elif algo in ("simulated_annealing", "hybrid"):
        # Placeholders until bonus steps are built
        raise NotImplementedError(f"Algorithm '{algo}' will be implemented in subsequent build steps.")
    else:
        raise ValueError(f"Unknown algorithm: '{algo}'")

    # 3. Re-validate candidate independently per DD-018
    if result.timetable is not None:
        validation_report = validate(
            timetable=result.timetable,
            dataset=dataset,
            soft_weights=config.soft_weights,
        )
        result.status = validation_report.status
        result.extra_metrics["validation_report"] = validation_report.to_dict()

    return result
