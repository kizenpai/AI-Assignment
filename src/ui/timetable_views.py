"""Timetable presentation views: Class-wise, Teacher-wise, and Room-wise grids.

Implements PRD FR-017, FR-018, FR-019, OBJ-011, and TRD Section K.2 / L.3:
- Single canonical schedule source (DD-029, current_timetable) ensuring cross-view consistency.
- Interactive multi-dimensional timetable matrices (Day x Period).
- Highlights lunch breaks, teacher unavailable slots, and free periods.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

from src.csp.models import Dataset, ScheduledSession, Timetable
from src.ui.dashboard import render_validation_dashboard


DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def build_grid_matrix(
    sessions: List[ScheduledSession],
    days: int,
    periods_per_day: int,
    lunch_period: Optional[int],
    cell_formatter,
    blocked_slots: Optional[set] = None,
) -> pd.DataFrame:
    """Construct a 2D matrix (Day rows x Period columns) for grid display."""
    blocked = blocked_slots or set()
    col_names = [f"Period {p}" for p in range(1, periods_per_day + 1)]
    row_names = [DAYS_OF_WEEK[d] if d < len(DAYS_OF_WEEK) else f"Day {d}" for d in range(days)]

    # Map (day, period) -> session
    slot_map: Dict[Tuple[int, int], ScheduledSession] = {}
    for s in sessions:
        for p in s.periods:
            slot_map[(s.day, p)] = s

    data = []
    for d in range(days):
        row = []
        for p in range(1, periods_per_day + 1):
            if lunch_period is not None and p == lunch_period:
                row.append("🍽️ Lunch")
            elif (d, p) in blocked:
                row.append("🚫 Unavailable")
            elif (d, p) in slot_map:
                row.append(cell_formatter(slot_map[(d, p)]))
            else:
                row.append("— Free —")
        data.append(row)

    return pd.DataFrame(data, index=row_names, columns=col_names)


def render_timetable_views_page() -> None:
    """Render the multi-perspective Timetable Views page."""
    st.header("📅 Timetable Views")
    st.write(
        "Inspect the generated schedule across three synchronized perspectives: "
        "Class-wise, Teacher-wise, and Room-wise (FR-017, FR-018, FR-019)."
    )

    timetable: Optional[Timetable] = st.session_state.get("current_timetable")
    dataset: Optional[Dataset] = st.session_state.get("dataset")

    if dataset is None or timetable is None or not timetable.scheduled_sessions:
        st.warning(
            "⚠️ No timetable is available to display! "
            "Please go to **Generate Timetable** and run an algorithm first."
        )
        return

    # View Mode Selection
    view_mode = st.radio(
        "Select Perspective",
        ["👥 Class-wise Timetable", "👨‍🏫 Teacher-wise Timetable", "🏫 Room-wise Timetable", "📋 Master Session Table"],
        horizontal=True,
    )

    st.markdown("---")

    # 1. Class-wise View
    if view_mode == "👥 Class-wise Timetable":
        st.subheader("👥 Student Class Schedule")
        class_ids = [c.class_id for c in dataset.classes]
        selected_cid = st.selectbox(
            "Select Class Group",
            class_ids,
            format_func=lambda cid: f"{cid} — {dataset.get_class(cid).name if dataset.get_class(cid) else ''}",
        )

        class_sessions = [s for s in timetable.scheduled_sessions if s.class_id == selected_cid]

        def format_class_cell(s: ScheduledSession) -> str:
            t = dataset.get_teacher(s.teacher_id)
            t_name = t.name if t else s.teacher_id
            return f"📘 {s.subject_id}\n👤 {t_name}\n📍 {s.room_id}"

        df = build_grid_matrix(
            sessions=class_sessions,
            days=dataset.days,
            periods_per_day=dataset.periods_per_day,
            lunch_period=dataset.lunch_period,
            cell_formatter=format_class_cell,
        )
        st.dataframe(df, use_container_width=True, height=280)
        st.caption(f"Showing {len(class_sessions)} scheduled periods for {selected_cid}.")

    # 2. Teacher-wise View
    elif view_mode == "👨‍🏫 Teacher-wise Timetable":
        st.subheader("👨‍🏫 Faculty Workload & Schedule")
        teacher_ids = [t.teacher_id for t in dataset.teachers]
        selected_tid = st.selectbox(
            "Select Faculty Member",
            teacher_ids,
            format_func=lambda tid: f"{tid} — {dataset.get_teacher(tid).name if dataset.get_teacher(tid) else ''}",
        )

        t_obj = dataset.get_teacher(selected_tid)
        teacher_sessions = [s for s in timetable.scheduled_sessions if s.teacher_id == selected_tid]
        blocked = {s.as_tuple() for s in t_obj.unavailable_slots} if t_obj else set()

        def format_teacher_cell(s: ScheduledSession) -> str:
            return f"👥 {s.class_id}\n📘 {s.subject_id}\n📍 {s.room_id}"

        df = build_grid_matrix(
            sessions=teacher_sessions,
            days=dataset.days,
            periods_per_day=dataset.periods_per_day,
            lunch_period=dataset.lunch_period,
            cell_formatter=format_teacher_cell,
            blocked_slots=blocked,
        )
        st.dataframe(df, use_container_width=True, height=280)

        # Faculty workload statistics
        total_teaching_periods = sum(s.duration_periods for s in teacher_sessions)
        col_w1, col_w2, col_w3 = st.columns(3)
        col_w1.metric("Assigned Periods / Week", total_teaching_periods)
        col_w2.metric("Max Weekly Limit", t_obj.max_weekly_periods if t_obj and t_obj.max_weekly_periods else "Unlimited")
        col_w3.metric("Max Daily Limit", t_obj.max_daily_periods if t_obj and t_obj.max_daily_periods else "Unlimited")

    # 3. Room-wise View
    elif view_mode == "🏫 Room-wise Timetable":
        st.subheader("🏫 Room Utilization Schedule")
        room_ids = [r.room_id for r in dataset.rooms]
        selected_rid = st.selectbox(
            "Select Room / Lab",
            room_ids,
            format_func=lambda rid: f"{rid} ({dataset.get_room(rid).room_type}, Cap: {dataset.get_room(rid).capacity})",
        )

        r_obj = dataset.get_room(selected_rid)
        room_sessions = [s for s in timetable.scheduled_sessions if s.room_id == selected_rid]
        blocked = {s.as_tuple() for s in r_obj.unavailable_slots} if r_obj else set()

        def format_room_cell(s: ScheduledSession) -> str:
            t = dataset.get_teacher(s.teacher_id)
            t_name = t.name if t else s.teacher_id
            return f"👥 {s.class_id} | 📘 {s.subject_id}\n👤 {t_name}"

        df = build_grid_matrix(
            sessions=room_sessions,
            days=dataset.days,
            periods_per_day=dataset.periods_per_day,
            lunch_period=dataset.lunch_period,
            cell_formatter=format_room_cell,
            blocked_slots=blocked,
        )
        st.dataframe(df, use_container_width=True, height=280)
        st.caption(f"Room {selected_rid} is occupied for {len(room_sessions)} periods this week.")

    # 4. Master Session Table
    else:
        st.subheader("📋 Master Timetable Session Log")
        session_rows = [
            {
                "Day": DAYS_OF_WEEK[s.day] if s.day < len(DAYS_OF_WEEK) else f"Day {s.day}",
                "Period": f"P{s.start_period}" if s.duration_periods == 1 else f"P{s.start_period}-P{s.start_period + s.duration_periods - 1}",
                "Class": s.class_id,
                "Subject": s.subject_id,
                "Teacher": dataset.get_teacher(s.teacher_id).name if dataset.get_teacher(s.teacher_id) else s.teacher_id,
                "Room": s.room_id,
                "Duration": f"{s.duration_periods}p",
                "Requirement ID": s.requirement_id,
            }
            for s in timetable.scheduled_sessions
        ]
        st.dataframe(pd.DataFrame(session_rows), use_container_width=True)

    # Embedded Validation Summary
    st.markdown("---")
    with st.expander("🔍 View Validation Audit for this Schedule", expanded=False):
        from src.csp.validator import validate
        val_rep = validate(timetable, dataset)
        render_validation_dashboard(
            result=st.session_state.get("generation_result"),
            timetable=timetable,
            validation_report=val_rep,
        )
