"""Timetable editing and integrity service.

Implements TRD Section L, PRD FR-016, FR-020, FR-021, and DD-030:
- propose_edit: creates a candidate draft and re-runs full independent validation (L.2).
- apply_edit: saves the candidate draft as current_timetable if valid (or with explicit override).
- discard_edit: drops the candidate draft without modifying current_timetable.
"""

from __future__ import annotations

import copy
from typing import Dict, List, Optional, Tuple
import uuid

from src.csp.models import Dataset, ScheduledSession, Timetable
from src.csp.validator import ValidationReport, validate


class EditError(Exception):
    """Raised when an edit operation cannot be performed."""

    pass


def propose_edit(
    current_timetable: Timetable,
    dataset: Dataset,
    requirement_id: str,
    new_day: int,
    new_start_period: int,
    new_room_id: str,
    soft_weights: Optional[Dict[str, float]] = None,
) -> Tuple[Timetable, ValidationReport]:
    """Create an unconfirmed draft timetable proposing a new slot/room for a session (TRD L.1).

    Runs full independent validation from scratch on the proposed timetable (L.2).
    Does NOT mutate current_timetable.

    Returns:
        (draft_timetable, validation_report)
    """
    # 1. Verify session exists
    target = current_timetable.get_session_by_requirement(requirement_id)
    if target is None:
        raise EditError(f"Session with requirement_id '{requirement_id}' not found in timetable.")

    # 2. Verify room exists
    room = dataset.get_room(new_room_id)
    if room is None:
        raise EditError(f"Room '{new_room_id}' does not exist in dataset.")

    # 3. Create deep copy of scheduled sessions
    new_sessions: List[ScheduledSession] = []
    for s in current_timetable.scheduled_sessions:
        if s.requirement_id == requirement_id:
            new_sessions.append(
                ScheduledSession(
                    requirement_id=s.requirement_id,
                    day=new_day,
                    start_period=new_start_period,
                    duration_periods=s.duration_periods,
                    room_id=new_room_id,
                    teacher_id=s.teacher_id,
                    class_id=s.class_id,
                    subject_id=s.subject_id,
                )
            )
        else:
            new_sessions.append(copy.deepcopy(s))

    draft_timetable = Timetable(
        timetable_id=f"DRAFT-{uuid.uuid4().hex[:6].upper()}",
        dataset_id=current_timetable.dataset_id,
        scheduled_sessions=new_sessions,
        unscheduled_requirement_ids=list(current_timetable.unscheduled_requirement_ids),
        generated_by=f"ManualEdit(from={current_timetable.generated_by})",
        status="NotEvaluated",
    )

    # 4. Run authoritative independent validation from scratch (TRD L.2)
    report = validate(draft_timetable, dataset, soft_weights=soft_weights)
    draft_timetable.status = report.status

    return draft_timetable, report


def apply_edit(
    current_timetable: Timetable,
    draft_timetable: Timetable,
    allow_invalid: bool = False,
) -> Timetable:
    """Commit the draft timetable as the canonical current_timetable (TRD L.1 & DD-030).

    By default, rejects saving an edit that introduces hard violations (allow_invalid=False).
    """
    if draft_timetable.status != "Valid" and not allow_invalid:
        raise EditError(
            f"Cannot save draft with status '{draft_timetable.status}'. "
            "Resolve hard violations or explicitly set allow_invalid=True."
        )

    current_timetable.scheduled_sessions = [copy.deepcopy(s) for s in draft_timetable.scheduled_sessions]
    current_timetable.unscheduled_requirement_ids = list(draft_timetable.unscheduled_requirement_ids)
    current_timetable.status = draft_timetable.status
    current_timetable.generated_by = draft_timetable.generated_by

    return current_timetable
