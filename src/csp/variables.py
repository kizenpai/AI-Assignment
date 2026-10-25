"""CSP Variable definitions.

Implements TRD Section G.1 & DD-009:
- Exactly one CSP variable per RequiredSession (DD-008).
- SessionVariable encapsulates requirement information and provides helpers for search heuristics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from src.csp.models import Dataset, RequiredSession


@dataclass
class SessionVariable:
    """A single CSP scheduling variable representing one required teaching session.

    Maps 1-to-1 with a RequiredSession (DD-008, DD-009).
    """

    requirement_id: str
    class_id: str
    subject_id: str
    teacher_id: str
    duration_periods: int = 1
    consecutive_required: bool = False
    occurrence_index: int = 1
    occurrence_total: int = 1

    @classmethod
    def from_required_session(cls, session: RequiredSession) -> "SessionVariable":
        return cls(
            requirement_id=session.requirement_id,
            class_id=session.class_id,
            subject_id=session.subject_id,
            teacher_id=session.teacher_id,
            duration_periods=session.duration_periods,
            consecutive_required=session.consecutive_required,
            occurrence_index=session.occurrence_index,
            occurrence_total=session.occurrence_total,
        )

    def shares_resource(self, other: "SessionVariable") -> bool:
        """Check if two variables share any resource (teacher or class).

        Used to calculate constraint degree for the Degree Heuristic.
        """
        if self.requirement_id == other.requirement_id:
            return False
        return self.teacher_id == other.teacher_id or self.class_id == other.class_id

    def __hash__(self) -> int:
        return hash(self.requirement_id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SessionVariable):
            return self.requirement_id == other.requirement_id
        return False

    def __str__(self) -> str:
        return f"Var({self.requirement_id}: {self.class_id} {self.subject_id} with {self.teacher_id})"


def build_variables(dataset: Dataset) -> List[SessionVariable]:
    """Construct the list of CSP variables from the dataset's required sessions.

    Enforces DD-009: X = { X_r : r in RequiredSessions }.
    """
    return [SessionVariable.from_required_session(rs) for rs in dataset.required_sessions]
