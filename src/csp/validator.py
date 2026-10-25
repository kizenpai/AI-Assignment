"""Independent timetable validator.

Implements TRD Section J, PRD FR-014, NFR-003, and NFR-004:
- Sole authority on timetable validity across the entire system.
- Completely independent of algorithm internal state, variable orders, or iteration counters.
- Pure function of (Timetable, Dataset) -> ValidationReport.
- Re-verifies all 10 hard constraints and computes itemized soft penalties.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.csp.constraints import ALL_HARD_CONSTRAINTS, Violation
from src.csp.models import Dataset, Timetable, TimetableStatus
from src.csp.soft_constraints import evaluate_soft_penalties


@dataclass
class ValidationReport:
    """Comprehensive validation and scoring report for a timetable (TRD J.3)."""

    status: TimetableStatus
    total_hard_violations: int
    violation_categories: Dict[str, int] = field(default_factory=dict)
    violations: List[Violation] = field(default_factory=list)
    soft_penalties: Dict[str, float] = field(default_factory=dict)
    total_soft_penalty: float = 0.0

    @property
    def is_valid(self) -> bool:
        """True strictly when all required sessions are scheduled and zero hard violations exist."""
        return self.status == "Valid"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "is_valid": self.is_valid,
            "total_hard_violations": self.total_hard_violations,
            "violation_categories": dict(self.violation_categories),
            "violations": [v.to_dict() for v in self.violations],
            "soft_penalties": dict(self.soft_penalties),
            "total_soft_penalty": self.total_soft_penalty,
        }

    def summary_text(self) -> str:
        if self.is_valid:
            return f"Valid (0 hard violations, soft penalty: {self.total_soft_penalty:.2f})"
        lines = [f"{self.status} ({self.total_hard_violations} hard violations)"]
        for cat, count in self.violation_categories.items():
            lines.append(f"  - {cat}: {count}")
        return "\n".join(lines)


def validate(
    timetable: Optional[Timetable],
    dataset: Dataset,
    soft_weights: Optional[Dict[str, float]] = None,
) -> ValidationReport:
    """Validate a candidate timetable against the authoritative dataset constraints (TRD J.2).

    Runs independently of any solver bookkeeping. Evaluates:
    - HC-001: Teacher Non-Overlap
    - HC-002: Class Non-Overlap
    - HC-003: Room Non-Overlap
    - HC-004: Room Capacity
    - HC-005: Room Type Compatibility
    - HC-006: Teacher Availability
    - HC-007: Completeness & Weekly Hours
    - HC-008: Teacher Max Workload
    - HC-009: Mandatory Lunch Break
    - HC-010: Laboratory Contiguity

    Determines status:
    - 'NoCandidate' if timetable is None
    - 'Incomplete' if required sessions are unplaced
    - 'Invalid' if any hard constraint violation exists
    - 'Valid' only if complete and zero hard violations exist
    """
    if timetable is None:
        return ValidationReport(
            status="NoCandidate",
            total_hard_violations=0,
            violation_categories={},
            violations=[],
            soft_penalties={},
            total_soft_penalty=0.0,
        )

    # 1. Run all registered hard constraints from scratch
    all_violations: List[Violation] = []
    for constraint in ALL_HARD_CONSTRAINTS:
        violations = constraint.evaluate(timetable, dataset)
        all_violations.extend(violations)

    # Categorize violations by constraint ID (e.g. {"HC-001": 2, "HC-004": 1})
    category_counts = dict(Counter(v.constraint_id for v in all_violations))

    # 2. Check completeness (HC-007 completeness aspect)
    scheduled_ids = {s.requirement_id for s in timetable.scheduled_sessions}
    all_req_ids = {r.requirement_id for r in dataset.required_sessions}
    has_unplaced_sessions = (
        len(scheduled_ids) < len(all_req_ids)
        or bool(timetable.unscheduled_requirement_ids)
    )

    # 3. Derive status
    if has_unplaced_sessions:
        status: TimetableStatus = "Incomplete"
    elif len(all_violations) > 0:
        status = "Invalid"
    else:
        status = "Valid"

    # Synchronize timetable status attribute if present
    timetable.status = status

    # 4. Evaluate soft penalties
    total_soft, soft_breakdown = evaluate_soft_penalties(
        timetable, dataset, weights=soft_weights
    )

    return ValidationReport(
        status=status,
        total_hard_violations=len(all_violations),
        violation_categories=category_counts,
        violations=all_violations,
        soft_penalties=soft_breakdown,
        total_soft_penalty=total_soft,
    )
