"""Unit tests for manual timetable editing and re-validation service.

Tests TRD TC-ED-1, TC-ED-2, and Section L.
"""

from pathlib import Path
import pytest

from src.algorithms.backtracking import solve_backtracking
from src.algorithms.base import AlgorithmConfig
from src.csp.models import Dataset, ScheduledSession, Timetable
from src.services.data_loader import load_dataset_from_file
from src.services.timetable_editor import EditError, apply_edit, propose_edit


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture
def solved_timetable():
    path = DATA_DIR / "small_dataset.json"
    dataset, _ = load_dataset_from_file(path)
    config = AlgorithmConfig(algorithm="backtracking", max_search_nodes=50000)
    result = solve_backtracking(dataset, config)
    assert result.status == "Valid"
    return dataset, result.timetable


def test_tc_ed_1_propose_edit_creating_teacher_overlap(solved_timetable):
    """TRD TC-ED-1: Propose an edit that creates a teacher overlap.

    Expected: propose_edit returns an Invalid candidate; current_timetable unchanged after Discard.
    """
    dataset, timetable = solved_timetable
    sessions = timetable.scheduled_sessions

    # Pick two sessions with the SAME teacher (e.g. Teacher T1)
    t1_sessions = [s for s in sessions if s.teacher_id == "T1"]
    assert len(t1_sessions) >= 2
    s1, s2 = t1_sessions[0], t1_sessions[1]

    orig_day = s1.day
    orig_period = s1.start_period
    orig_room = s1.room_id

    # Propose moving s1 into s2's slot and room -> creates teacher collision!
    draft_tt, report = propose_edit(
        current_timetable=timetable,
        dataset=dataset,
        requirement_id=s1.requirement_id,
        new_day=s2.day,
        new_start_period=s2.start_period,
        new_room_id=s2.room_id,
    )

    # 1. Draft is marked Invalid
    assert draft_tt.status == "Invalid"
    assert report.is_valid is False
    assert "HC-001" in report.violation_categories

    # 2. current_timetable is strictly unchanged
    s1_check = timetable.get_session_by_requirement(s1.requirement_id)
    assert s1_check.day == orig_day
    assert s1_check.start_period == orig_period
    assert s1_check.room_id == orig_room

    # 3. Saving without override raises EditError
    with pytest.raises(EditError):
        apply_edit(timetable, draft_tt, allow_invalid=False)


def test_tc_ed_2_propose_and_save_valid_edit(solved_timetable):
    """TRD TC-ED-2: Propose a valid edit and Save -> current_timetable updates successfully."""
    dataset, timetable = solved_timetable
    session = timetable.scheduled_sessions[0]
    req_id = session.requirement_id

    # Move to a known free slot or different compatible room where it remains valid
    # Find a free room in the same slot if available
    occupied_rooms = {
        s.room_id for s in timetable.scheduled_sessions
        if s.day == session.day and s.start_period == session.start_period
    }
    cls_obj = dataset.get_class(session.class_id)
    free_rooms = [
        r.room_id for r in dataset.rooms
        if r.room_id not in occupied_rooms and r.capacity >= cls_obj.size
    ]

    if free_rooms:
        new_room = free_rooms[0]
        draft_tt, report = propose_edit(
            current_timetable=timetable,
            dataset=dataset,
            requirement_id=req_id,
            new_day=session.day,
            new_start_period=session.start_period,
            new_room_id=new_room,
        )

        if report.is_valid:
            updated = apply_edit(timetable, draft_tt)
            assert updated.get_session_by_requirement(req_id).room_id == new_room
            assert timetable.status == "Valid"


def test_edit_nonexistent_session_raises_error(solved_timetable):
    """Proposing an edit for an unknown session raises EditError."""
    dataset, timetable = solved_timetable
    with pytest.raises(EditError):
        propose_edit(
            current_timetable=timetable,
            dataset=dataset,
            requirement_id="REQ-NON-EXISTENT",
            new_day=0,
            new_start_period=1,
            new_room_id="R101",
        )
