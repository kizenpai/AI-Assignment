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

    # Placeholder: each page will delegate to a function in src/ui/*.
    st.info(f"🚧 **{page}** page — coming soon in later build steps.")


if __name__ == "__main__":
    main()
