"""Algorithm selection and timetable generation UI page.

Implements PRD FR-006, FR-007, FR-026, FR-027, and TRD Section K.2.
"""

from __future__ import annotations

import streamlit as st

from src.algorithms.base import AlgorithmConfig
from src.services.timetable_generator import generate
from src.ui.dashboard import render_validation_dashboard


def render_generator_page() -> None:
    """Render the Algorithm Selection & Timetable Generation page."""
    st.header("⚡ Generate Timetable")
    st.write(
        "Select an artificial intelligence scheduling algorithm and configure search parameters "
        "to synthesize an optimal academic timetable."
    )

    dataset = st.session_state.get("dataset")
    if dataset is None:
        st.warning(
            "⚠️ No dataset is currently loaded! "
            "Please go to **Dataset & Validation** in the sidebar to load or upload a dataset first."
        )
        return

    # Dataset status indicator
    ds_name = st.session_state.get("dataset_source_name", dataset.dataset_id)
    st.info(
        f"📋 Active Dataset: **{ds_name}** | "
        f"{len(dataset.classes)} Classes | {len(dataset.teachers)} Teachers | "
        f"{len(dataset.required_sessions)} Required Sessions"
    )

    st.markdown("---")
    st.subheader("1. Select Algorithm (FR-006)")

    algo_options = [
        "Backtracking CSP (MRV + Degree + FC)",
        "Min-Conflicts Local Search",
        "Simulated Annealing (Bonus - Step 9)",
        "Hybrid CSP + SA (Bonus - Step 9)",
    ]

    selected_algo_label = st.radio(
        "Scheduling Algorithm",
        algo_options,
        index=0,
        help="Choose between systematic CSP search or stochastic local search.",
    )

    # Configure algorithm parameters
    st.markdown("---")
    st.subheader("2. Search Parameters")

    config = AlgorithmConfig()

    if selected_algo_label == "Backtracking CSP (MRV + Degree + FC)":
        config.algorithm = "backtracking"
        st.caption(
            "Systematic depth-first constraint satisfaction with heuristic variable ordering "
            "and forward checking domain pruning."
        )

        col_h1, col_h2, col_h3 = st.columns(3)
        with col_h1:
            config.use_mrv = st.checkbox(
                "Minimum Remaining Values (MRV)",
                value=True,
                help="Prioritize variables with the fewest remaining legal time slots.",
            )
        with col_h2:
            config.use_degree_heuristic = st.checkbox(
                "Degree Heuristic",
                value=True,
                help="Break MRV ties by selecting variables that share resources with the most unassigned variables.",
            )
        with col_h3:
            config.use_forward_checking = st.checkbox(
                "Forward Checking (FC)",
                value=True,
                help="Prune inconsistent values from neighbor domains to detect dead ends early.",
            )

        col_l1, col_l2 = st.columns(2)
        with col_l1:
            config.max_search_nodes = st.number_input(
                "Max Search Nodes (Resource Budget)",
                min_value=100,
                max_value=1_000_000,
                value=200_000,
                step=10_000,
                help="Configurable search limit (NFR-002). Reaching this limit produces a search_limit status.",
            )

    elif selected_algo_label == "Min-Conflicts Local Search":
        config.algorithm = "min_conflicts"
        st.caption(
            "Iterative repair local search that begins from a complete assignment and resolves conflicts."
        )

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            config.max_iterations = st.number_input(
                "Max Iterations",
                min_value=100,
                max_value=50_000,
                value=5000,
                step=500,
                help="Maximum number of conflict-repair steps to perform.",
            )
        with col_m2:
            config.random_seed = st.number_input(
                "Random Seed",
                min_value=0,
                max_value=999999,
                value=42,
                step=1,
                help="Seed for deterministic reproducibility (NFR-015).",
            )

    else:
        st.warning("⚠️ This bonus algorithm will be implemented in Step 9.")
        return

    st.markdown("---")

    # Generate button
    if st.button("🚀 Generate Timetable", type="primary", use_container_width=True):
        with st.spinner(f"Running {config.algorithm.capitalize()} solver... Please wait."):
            try:
                result = generate(dataset, config)
                st.session_state["generation_result"] = result
                st.session_state["current_timetable"] = result.timetable

                val_rep = result.extra_metrics.get("validation_report")
                if val_rep:
                    from src.csp.validator import ValidationReport
                    # Reconstruct or store report
                    st.session_state["validation_report_obj"] = result.extra_metrics.get("validation_report")

                if result.is_success:
                    st.balloons()
                    st.success(
                        f"✅ Generation Complete in {result.runtime_seconds:.3f} seconds! "
                        f"Timetable is valid and ready for review in 'View Timetable'."
                    )
                elif result.termination == "exhausted":
                    st.error("❌ Search space exhausted: No feasible schedule exists for this dataset.")
                elif result.termination == "search_limit":
                    st.warning("⚠️ Search limit reached: Returned best candidate found within budget.")
                else:
                    st.error(f"Generation terminated: {result.termination}")

            except Exception as e:
                st.error(f"Error during generation: {e}")

    # Render dashboard if result exists
    if "generation_result" in st.session_state:
        st.markdown("---")
        gen_res = st.session_state["generation_result"]
        from src.csp.validator import validate
        val_rep = validate(gen_res.timetable, dataset) if gen_res.timetable else None
        render_validation_dashboard(
            result=gen_res,
            timetable=gen_res.timetable,
            validation_report=val_rep,
        )
