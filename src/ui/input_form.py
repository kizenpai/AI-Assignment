"""Dataset loading and validation UI component (PRD FR-001..FR-005).

Provides controls to choose a bundled sample dataset or upload a custom JSON dataset,
runs structural validation, displays metric cards and entity tables, and distinguishes
blocking errors from non-blocking warnings.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

from src.csp.models import Dataset
from src.services.data_loader import (
    DatasetParseError,
    load_dataset_from_file,
    load_dataset_from_json,
)
from src.services.data_validator import DatasetValidationReport


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

SAMPLE_DATASETS = {
    "Small Feasible Dataset (small_v1)": DATA_DIR / "small_dataset.json",
    "Large Scale Dataset (large_v1)": DATA_DIR / "large_dataset.json",
    "Infeasible Dataset (infeasible_sample_v1)": DATA_DIR / "infeasible_sample.json",
    "Template Dataset": DATA_DIR / "sample_input_template.json",
}


def render_dataset_page() -> None:
    """Render the Dataset & Validation page."""
    st.header("📂 Dataset Selection & Validation")
    st.write(
        "Upload a custom JSON timetable configuration or select a bundled sample dataset. "
        "The application performs full structural and referential integrity validation before generation."
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        data_source = st.radio(
            "Data Source",
            ["Bundled Sample Dataset", "Upload Custom JSON"],
            horizontal=True,
        )

    current_dataset: Optional[Dataset] = None
    report: Optional[DatasetValidationReport] = None

    if data_source == "Bundled Sample Dataset":
        with col2:
            selected_sample_name = st.selectbox(
                "Choose a sample dataset",
                list(SAMPLE_DATASETS.keys()),
                index=0,
            )

        sample_path = SAMPLE_DATASETS[selected_sample_name]
        try:
            current_dataset, report = load_dataset_from_file(sample_path)
            st.session_state["dataset"] = current_dataset
            st.session_state["validation_report"] = report
            st.session_state["dataset_source_name"] = selected_sample_name
        except Exception as e:
            st.error(f"Failed to load bundled dataset: {e}")
            return

    else:
        with col2:
            uploaded_file = st.file_uploader(
                "Upload Dataset JSON",
                type=["json"],
                help="Max size 5MB. Must match TRD Section F JSON schema.",
            )

        if uploaded_file is not None:
            try:
                content = uploaded_file.read().decode("utf-8")
                current_dataset, report = load_dataset_from_json(content)
                st.session_state["dataset"] = current_dataset
                st.session_state["validation_report"] = report
                st.session_state["dataset_source_name"] = uploaded_file.name
                st.success(f"Uploaded and parsed `{uploaded_file.name}` successfully.")
            except DatasetParseError as pe:
                st.error(f"❌ JSON Parse Error: {pe}")
                return
            except Exception as e:
                st.error(f"❌ Unexpected Error: {e}")
                return
        elif "dataset" in st.session_state:
            current_dataset = st.session_state["dataset"]
            report = st.session_state.get("validation_report")

    if current_dataset is None or report is None:
        st.info("👆 Please select or upload a dataset above to proceed.")
        return

    # Validation Status Banner
    st.markdown("---")
    st.subheader("🔍 Validation Report (FR-005)")

    if report.is_valid:
        st.success(
            f"✅ **Dataset `{current_dataset.dataset_id}` is structurally valid.** "
            f"Ready for CSP timetable generation. (0 blocking errors, {report.warning_count} warnings)"
        )
    else:
        st.error(
            f"❌ **Dataset `{current_dataset.dataset_id}` has {report.error_count} blocking error(s).** "
            "Timetable generation cannot proceed until these errors are resolved."
        )

    # Detailed Errors & Warnings
    if report.errors:
        with st.expander(f"🚨 Blocking Errors ({len(report.errors)})", expanded=True):
            for err in report.errors:
                st.markdown(f"- **[{err.code}]** {err.message}")

    if report.warnings:
        with st.expander(f"⚠️ Warnings ({len(report.warnings)})", expanded=False):
            for w in report.warnings:
                st.markdown(f"- **[{w.code}]** {w.message}")

    # Dataset Summary Metrics
    st.markdown("---")
    st.subheader("📊 Dataset Overview")
    st.caption(f"**Description:** {current_dataset.description}")

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Classes", len(current_dataset.classes))
    m2.metric("Teachers", len(current_dataset.teachers))
    m3.metric("Rooms", len(current_dataset.rooms))
    m4.metric("Subjects", len(current_dataset.subjects))
    m5.metric("Required Sessions", len(current_dataset.required_sessions))
    m6.metric("Week Schedule", f"{current_dataset.days}d × {current_dataset.periods_per_day}p")

    # Detailed Entity Tables
    tab_reqs, tab_teachers, tab_classes, tab_rooms, tab_json = st.tabs([
        "📋 Requirements & Sessions",
        "👨‍🏫 Teachers & Availability",
        "👥 Classes",
        "🏫 Rooms",
        "📄 Raw JSON",
    ])

    with tab_reqs:
        st.markdown(f"**Total Weekly Teaching Hours:** {current_dataset.total_required_periods} periods")
        req_rows = [
            {
                "Class": r.class_id,
                "Subject": r.subject_id,
                "Teacher": r.teacher_id,
                "Weekly Periods": r.weekly_periods,
                "Duration": r.duration_periods,
                "Consecutive": "Yes" if r.consecutive_required else "No",
            }
            for r in current_dataset.requirements
        ]
        if req_rows:
            st.dataframe(pd.DataFrame(req_rows), use_container_width=True)

        with st.expander(f"🔎 View Expanded CSP Variables / RequiredSessions ({len(current_dataset.required_sessions)})"):
            sess_rows = [
                {
                    "Requirement ID": s.requirement_id,
                    "Class": s.class_id,
                    "Subject": s.subject_id,
                    "Teacher": s.teacher_id,
                    "Duration": s.duration_periods,
                    "Occurrence": f"{s.occurrence_index} / {s.occurrence_total}",
                }
                for s in current_dataset.required_sessions
            ]
            st.dataframe(pd.DataFrame(sess_rows), use_container_width=True)

    with tab_teachers:
        teacher_rows = [
            {
                "Teacher ID": t.teacher_id,
                "Name": t.name,
                "Subjects": ", ".join(t.subjects_qualified),
                "Max Daily": t.max_daily_periods if t.max_daily_periods else "None",
                "Max Weekly": t.max_weekly_periods if t.max_weekly_periods else "None",
                "Unavailable Slots": len(t.unavailable_slots),
                "Preferred Slots": len(t.preferred_slots),
            }
            for t in current_dataset.teachers
        ]
        if teacher_rows:
            st.dataframe(pd.DataFrame(teacher_rows), use_container_width=True)

    with tab_classes:
        class_rows = [
            {
                "Class ID": c.class_id,
                "Name": c.name,
                "Size (Students)": c.size,
                "Calendar": c.calendar_id,
            }
            for c in current_dataset.classes
        ]
        if class_rows:
            st.dataframe(pd.DataFrame(class_rows), use_container_width=True)

    with tab_rooms:
        room_rows = [
            {
                "Room ID": r.room_id,
                "Capacity": r.capacity,
                "Type": r.room_type,
                "Blocked Slots": len(r.unavailable_slots),
            }
            for r in current_dataset.rooms
        ]
        if room_rows:
            st.dataframe(pd.DataFrame(room_rows), use_container_width=True)

    with tab_json:
        st.json(current_dataset.to_dict())
