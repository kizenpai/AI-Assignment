"""Soft constraint definitions and penalty calculators for the AI Timetable Scheduler.

Implements TRD Section G.5 & I.3:
- SC-001: Minimize class gaps (idle periods between classes).
- SC-002: Distribute subjects evenly across days for each class.
- SC-003: Limit consecutive teaching periods for faculty (default max 3, ASM-T003).
- SC-004: Respect teacher slot preferences (undesired slots penalty).
- SC-005: Lab continuity preference for single-period practicals.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from src.csp.models import Dataset, ScheduledSession, Timetable


DEFAULT_SOFT_WEIGHTS: Dict[str, float] = {
    "SC-001": 1.0,  # Minimize class gaps
    "SC-002": 1.0,  # Subject distribution across days
    "SC-003": 0.75, # Limit consecutive teaching periods
    "SC-004": 0.5,  # Teacher time preferences
    "SC-005": 1.0,  # Lab continuity preference
}


# ============================================================================
# SC-001: Minimize Class Gaps
# ============================================================================
def calculate_class_gaps_penalty(timetable: Timetable, dataset: Dataset) -> float:
    """SC-001: Count empty periods strictly between first and last scheduled period of each class.

    Excludes the designated lunch period.
    """
    # Group occupied periods by (class_id, day)
    class_days: Dict[Tuple[str, int], Set[int]] = defaultdict(set)
    for s in timetable.scheduled_sessions:
        for p in s.periods:
            class_days[(s.class_id, s.day)].add(p)

    lunch = dataset.lunch_period
    total_gaps = 0

    for (cid, day), periods in class_days.items():
        if len(periods) <= 1:
            continue
        min_p = min(periods)
        max_p = max(periods)

        for p in range(min_p, max_p + 1):
            if p not in periods:
                if lunch is not None and p == lunch:
                    continue  # Lunch break is not penalized as an idle gap
                total_gaps += 1

    return float(total_gaps)


# ============================================================================
# SC-002: Distribute Subjects Across Days
# ============================================================================
def calculate_subject_distribution_penalty(timetable: Timetable, dataset: Dataset) -> float:
    """SC-002: Penalize clustering multiple occurrences of the same subject on the same day."""
    # Count (class_id, subject_id, day) -> count of scheduled sessions
    counts: Dict[Tuple[str, str, int], int] = defaultdict(int)
    for s in timetable.scheduled_sessions:
        counts[(s.class_id, s.subject_id, s.day)] += 1

    penalty = 0.0
    for (cid, sid, day), count in counts.items():
        if count > 1:
            # Quadratic penalty for severe clustering
            penalty += float((count - 1) ** 2)

    return penalty


# ============================================================================
# SC-003: Limit Consecutive Teaching Periods
# ============================================================================
def calculate_consecutive_teaching_penalty(
    timetable: Timetable,
    dataset: Dataset,
    max_consecutive: int = 3,
) -> float:
    """SC-003: Penalize teachers scheduled for more than max_consecutive periods back-to-back (ASM-T003)."""
    # Map (teacher_id, day) -> set of occupied periods
    teacher_days: Dict[Tuple[str, int], Set[int]] = defaultdict(set)
    for s in timetable.scheduled_sessions:
        for p in s.periods:
            teacher_days[(s.teacher_id, s.day)].add(p)

    penalty = 0.0

    for (tid, day), periods in teacher_days.items():
        if not periods:
            continue
        sorted_periods = sorted(periods)
        current_streak = 0
        prev_p: Optional[int] = None

        for p in sorted_periods:
            if prev_p is not None and p == prev_p + 1:
                current_streak += 1
            else:
                current_streak = 1
            prev_p = p

            if current_streak > max_consecutive:
                penalty += 1.0

    return penalty


# ============================================================================
# SC-004: Teacher Time Preferences
# ============================================================================
def calculate_teacher_preferences_penalty(timetable: Timetable, dataset: Dataset) -> float:
    """SC-004: Penalize assigning teachers to their declared undesired slots."""
    teacher_undesired: Dict[str, Set[Tuple[int, int]]] = {
        t.teacher_id: {s.as_tuple() for s in t.undesired_slots} for t in dataset.teachers
    }

    penalty = 0.0
    for s in timetable.scheduled_sessions:
        undesired = teacher_undesired.get(s.teacher_id, set())
        for p in s.periods:
            if (s.day, p) in undesired:
                penalty += 1.0

    return penalty


# ============================================================================
# SC-005: Lab Continuity Preference
# ============================================================================
def calculate_lab_continuity_penalty(timetable: Timetable, dataset: Dataset) -> float:
    """SC-005: For lab subjects with consecutive_required=False, prefer back-to-back scheduling."""
    # Find all sessions of lab subjects
    lab_subject_ids = {s.subject_id for s in dataset.subjects if s.is_lab}
    if not lab_subject_ids:
        return 0.0

    # Group by (class_id, subject_id, day)
    lab_sessions: Dict[Tuple[str, str, int], List[ScheduledSession]] = defaultdict(list)
    for s in timetable.scheduled_sessions:
        if s.subject_id in lab_subject_ids and not dataset.get_subject(s.subject_id).is_lab:
            continue
        if s.subject_id in lab_subject_ids:
            lab_sessions[(s.class_id, s.subject_id, s.day)].append(s)

    penalty = 0.0
    # If multiple 1-period lab sessions occur in a day, verify they are adjacent
    for (cid, sid, day), sessions in lab_sessions.items():
        if len(sessions) > 1:
            periods = sorted(p for s in sessions for p in s.periods)
            for i in range(len(periods) - 1):
                if periods[i + 1] != periods[i] + 1:
                    penalty += 1.0

    return penalty


def evaluate_soft_penalties(
    timetable: Timetable,
    dataset: Dataset,
    weights: Optional[Dict[str, float]] = None,
) -> Tuple[float, Dict[str, float]]:
    """Calculate the aggregate weighted soft constraint penalty and itemized breakdown (TRD I.3).

    Returns:
        (total_weighted_penalty, breakdown_dict) where breakdown_dict has entries for SC-001..SC-005.
    """
    w = dict(DEFAULT_SOFT_WEIGHTS)
    if weights:
        w.update(weights)

    raw_penalties = {
        "SC-001": calculate_class_gaps_penalty(timetable, dataset),
        "SC-002": calculate_subject_distribution_penalty(timetable, dataset),
        "SC-003": calculate_consecutive_teaching_penalty(timetable, dataset),
        "SC-004": calculate_teacher_preferences_penalty(timetable, dataset),
        "SC-005": calculate_lab_continuity_penalty(timetable, dataset),
    }

    weighted_breakdown = {k: v * w.get(k, 1.0) for k, v in raw_penalties.items()}
    total = sum(weighted_breakdown.values())

    return total, weighted_breakdown
