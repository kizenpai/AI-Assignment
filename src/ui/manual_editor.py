"""Manual timetable editor and export UI component.

Implements TRD Section L, PRD FR-016, FR-020, FR-021, FR-022, OBJ-012, and OBJ-013:
- Propose edit -> immediate independent re-validation feedback.
- Save confirmed edit (updates current_timetable) or Discard draft.
- Download buttons for CSV and Excel (.xlsx) formats.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import streamlit as st

from src.csp.models import Dataset, ScheduledSession, Timetable
from src.services.export import ExportError, to_csv, to_excel
from src.services.timetable_editor import EditError, apply_edit, propose_edit
from src.ui.dashboard import render_validation_dashboard

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def render_editor_page() -> None:
    """Render the Manual Schedule Editor & Export page."""
    st.header("✏️ Manual Timetable Editor & Export")
    st.write(
        "Make targeted manual adjustments to scheduled sessions. "
        "Every change is immediately checked through the independent validator before committing (FR-016, FR-020)."
    )

    timetable: Optional[Timetable] = st.session_state.get("current_timetable")
    dataset: Optional[Dataset] = st.session_state.get("dataset")

    if dataset is None or timetable is None or not timetable.scheduled_sessions:
        st.warning(
            "⚠️ No active timetable is available to edit! "
            "Please load a dataset and generate a timetable first."
        )
        return

    col_edit, col_export = st.columns([1.6, 1.0])

    with col_edit:
        st.subheader("1. Propose Session Relocation")

        # Select Class, then session
        class_ids = sorted(list({s.class_id for s in timetable.scheduled_sessions}))
        selected_cid = st.selectbox("Select Class", class_ids)

        class_sessions = [s for s in timetable.scheduled_sessions if s.class_id == selected_cid]
        session_labels = {
            s.requirement_id: (
                f"{s.requirement_id}: {s.subject_id} with "
                f"{dataset.get_teacher(s.teacher_id).name if dataset.get_teacher(s.teacher_id) else s.teacher_id} "
                f"[{DAYS_OF_WEEK[s.day]} P{s.start_period}, {s.room_id}]"
            )
            for s in class_sessions
        }

        selected_req_id = st.selectbox(
            "Select Scheduled Session to Move",
            list(session_labels.keys()),
            format_func=lambda req_id: session_labels[req_id],
        )

        current_session = timetable.get_session_by_requirement(selected_req_id)
        if current_session:
            st.info(
                f"**Current Assignment:** {DAYS_OF_WEEK[current_session.day]}, "
                f"Period {current_session.start_period} ({current_session.duration_periods}p block), "
                f"Room `{current_session.room_id}`"
            )

        # Propose new targets
        st.markdown("**Select New Coordinates:**")
        c_day, c_per, c_room = st.columns(3)

        with c_day:
            new_day = st.selectbox(
                "New Day",
                range(dataset.days),
                index=current_session.day if current_session else 0,
                format_func=lambda d: DAYS_OF_WEEK[d] if d < len(DAYS_OF_WEEK) else f"Day {d}",
            )

        with c_per:
            max_start = dataset.periods_per_day - (current_session.duration_periods if current_session else 1) + 1
            new_start_period = st.selectbox(
                "New Start Period",
                range(1, max_start + 1),
                index=min((current_session.start_period if current_session else 1) - 1, max_start - 1),
                format_func=lambda p: f"Period {p}",
            )

        with c_room:
            room_ids = [r.room_id for r in dataset.rooms]
            default_room_idx = room_ids.index(current_session.room_id) if current_session and current_session.room_id in room_ids else 0
            new_room_id = st.selectbox("New Room", room_ids, index=default_room_idx)

        # Propose edit button
        if st.button("🔍 Propose & Validate Edit", use_container_width=True):
            try:
                draft_tt, val_report = propose_edit(
                    current_timetable=timetable,
                    dataset=dataset,
                    requirement_id=selected_req_id,
                    new_day=new_day,
                    new_start_period=new_start_period,
                    new_room_id=new_room_id,
                )
                st.session_state["draft_timetable"] = draft_tt
                st.session_state["draft_validation_report"] = val_report

                if val_report.is_valid:
                    st.success("✅ Proposed edit is completely VALID! You can safely apply it below.")
                else:
                    st.error(
                        f"❌ Proposed edit creates {val_report.total_hard_violations} hard violation(s). "
                        "Saving is restricted by default."
                    )
            except EditError as ee:
                st.error(f"Edit Error: {ee}")

        # Render Draft Confirmation Controls
        draft = st.session_state.get("draft_timetable")
        draft_report = st.session_state.get("draft_validation_report")

        if draft is not None and draft_report is not None:
            st.markdown("---")
            st.markdown(f"**Draft Preview Status:** `{draft.status}`")

            if draft_report.violations:
                st.caption("Violations introduced by proposed edit:")
                for v in draft_report.violations[:3]:
                    st.markdown(f"- 🚨 **[{v.constraint_id}]** {v.message}")

            col_save, col_discard = st.columns(2)
            with col_save:
                allow_override = False
                if not draft_report.is_valid:
                    allow_override = st.checkbox("Force save despite violations (Override)", value=False)

                if st.button("💾 Apply & Commit Changes", type="primary", use_container_width=True):
                    try:
                        apply_edit(timetable, draft, allow_invalid=allow_override)
                        st.session_state["current_timetable"] = timetable
                        del st.session_state["draft_timetable"]
                        del st.session_state["draft_validation_report"]
                        st.success("✅ Changes committed to canonical timetable! View updated tables in 'View Timetable'.")
                        st.rerun()
                    except EditError as ee:
                        st.error(str(ee))

            with col_discard:
                if st.button("❌ Discard Draft", use_container_width=True):
                    del st.session_state["draft_timetable"]
                    del st.session_state["draft_validation_report"]
                    st.info("Draft discarded. Timetable left untouched.")
                    st.rerun()

    # Right column: Exporting
    with col_export:
        st.subheader("2. Export Timetable (FR-022)")
        st.write("Download the current canonical schedule for external distribution.")

        is_valid = (timetable.status == "Valid")

        if is_valid:
            st.success("✅ Schedule is verified VALID for export.")
        else:
            st.warning(
                f"⚠️ Current schedule has status `{timetable.status}`. "
                "Exports require explicit confirmation banner (DD-031)."
            )

        allow_invalid_exp = False
        if not is_valid:
            allow_invalid_exp = st.checkbox("Allow export of invalid draft", value=False)

        try:
            csv_data = to_csv(timetable, dataset, allow_invalid_export=allow_invalid_exp)
            st.download_button(
                label="📥 Download CSV (.csv)",
                data=csv_data,
                file_name=f"timetable_{dataset.dataset_id}.csv",
                mime="text/csv",
                use_container_width=True,
                disabled=(not is_valid and not allow_invalid_exp),
            )
        except ExportError as ee:
            st.caption(f"CSV export locked: {ee}")

        try:
            excel_data = to_excel(timetable, dataset, allow_invalid_export=allow_invalid_exp)
            st.download_button(
                label="📊 Download Excel (.xlsx)",
                data=excel_data,
                file_name=f"timetable_{dataset.dataset_id}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                disabled=(not is_valid and not allow_invalid_exp),
            )
        except ExportError as ee:
            st.caption(f"Excel export locked: {ee}")
