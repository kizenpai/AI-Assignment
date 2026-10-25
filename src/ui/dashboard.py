"""Dashboard component for displaying validation results and algorithm metrics.

Implements TRD Section K.2, PRD FR-014, FR-015, FR-026, and FR-027.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import streamlit as st

from src.algorithms.base import AlgorithmResult
from src.csp.models import Timetable
from src.csp.validator import ValidationReport


def render_validation_dashboard(
    result: Optional[AlgorithmResult] = None,
    timetable: Optional[Timetable] = None,
    validation_report: Optional[ValidationReport] = None,
) -> None:
    """Render a comprehensive dashboard displaying schedule validity, metrics, and constraint breakdowns."""
    if result is None and timetable is None:
        st.info("No timetable has been generated or selected yet. Please run timetable generation first.")
        return

    # Extract metrics
    runtime = result.runtime_seconds if result else 0.0
    nodes_or_iters = result.search_nodes_or_iterations if result else 0
    algo_name = result.config_used.algorithm if result else (timetable.generated_by if timetable else "Unknown")
    status = validation_report.status if validation_report else (result.status if result else "NotEvaluated")
    hard_violations = validation_report.total_hard_violations if validation_report else 0
    soft_penalty = validation_report.total_soft_penalty if validation_report else 0.0

    # 1. Status Banner
    st.markdown("### 🏆 Timetable Validation & Quality")
    if status == "Valid":
        st.success(
            f"🎉 **Status: VALID** — Zero hard-constraint violations detected! "
            f"All required teaching sessions have been successfully scheduled."
        )
    elif status == "Incomplete":
        st.warning(
            f"⚠️ **Status: INCOMPLETE** — The algorithm terminated before placing all required sessions."
        )
    elif status == "Invalid":
        st.error(
            f"❌ **Status: INVALID** — {hard_violations} hard-constraint violation(s) detected. "
            f"This schedule cannot be deployed as an academic timetable."
        )
    else:
        st.info(f"ℹ️ **Status: {status}**")

    # 2. Performance & Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Algorithm", algo_name.capitalize())
    c2.metric("Runtime", f"{runtime:.3f} s" if runtime < 60 else f"{runtime / 60:.2f} min")
    c3.metric(
        "Search Effort",
        f"{nodes_or_iters:,} {'nodes' if 'backtrack' in algo_name else 'iterations'}",
    )
    c4.metric(
        "Quality (Soft Penalty)",
        f"{soft_penalty:.2f}",
        delta=f"-{hard_violations} Hard Violations" if hard_violations > 0 else "0 Hard Violations",
        delta_color="inverse" if hard_violations > 0 else "normal",
    )

    # 3. Breakdown Tabs
    tab_hard, tab_soft = st.tabs(["🚨 Hard Constraint Audit", "✨ Soft Penalty Breakdown"])

    with tab_hard:
        if validation_report and validation_report.violations:
            st.markdown(f"**Found {len(validation_report.violations)} violation(s):**")
            violation_rows = [
                {
                    "Constraint": v.constraint_id,
                    "Message": v.message,
                    "Sessions": ", ".join(v.session_ids),
                    "Resources": ", ".join(f"{k}={val}" for k, val in v.resource_ids.items()),
                }
                for v in validation_report.violations
            ]
            st.dataframe(pd.DataFrame(violation_rows), use_container_width=True)
        else:
            st.success("✅ Clean audit: All 10 hard constraints (HC-001 through HC-010) fully satisfied.")

    with tab_soft:
        if validation_report and validation_report.soft_penalties:
            st.markdown("**Soft Constraint Inspection (PRD FR-015):**")
            soft_labels = {
                "SC-001": "Minimize Class Gaps (idle periods between classes)",
                "SC-002": "Subject Distribution (avoid same-subject clustering)",
                "SC-003": "Faculty Workload Spacing (limit consecutive periods)",
                "SC-004": "Teacher Time Preferences (avoid undesired slots)",
                "SC-005": "Lab Continuity (consecutive practicals preference)",
            }
            soft_rows = [
                {
                    "Constraint ID": sc_id,
                    "Description": soft_labels.get(sc_id, "Soft preference"),
                    "Weighted Penalty": f"{val:.2f}",
                }
                for sc_id, val in validation_report.soft_penalties.items()
            ]
            st.dataframe(pd.DataFrame(soft_rows), use_container_width=True)
        else:
            st.info("No soft constraint metrics available.")
