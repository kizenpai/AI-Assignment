"""
app.py — Streamlit entry point.

This file only handles page routing and top-level layout.
All business logic lives in src/services/ and src/csp/.
All UI rendering lives in src/ui/.

Run with:  streamlit run app.py
"""

import streamlit as st


def main():
    st.set_page_config(
        page_title="AI Timetable Scheduler",
        page_icon="📅",
        layout="wide",
    )

    st.title("📅 AI-Based Timetable Scheduler")
    st.caption("Constraint Satisfaction & Optimization — Academic Project")

    # Sidebar navigation — pages will be added as we build each module.
    page = st.sidebar.radio(
        "Navigate",
        [
            "Dataset & Validation",
            "Generate Timetable",
            "View Timetable",
            "Manual Editor",
            "Experiments",
        ],
    )

    if page == "Dataset & Validation":
        from src.ui.input_form import render_dataset_page
        render_dataset_page()
    elif page == "Generate Timetable":
        from src.ui.algorithm_selector import render_generator_page
        render_generator_page()
    elif page == "View Timetable":
        from src.ui.timetable_views import render_timetable_views_page
        render_timetable_views_page()
    elif page == "Manual Editor":
        from src.ui.manual_editor import render_editor_page
        render_editor_page()
    else:
        st.info(f"🚧 **{page}** page — coming soon in later build steps.")


if __name__ == "__main__":
    main()
