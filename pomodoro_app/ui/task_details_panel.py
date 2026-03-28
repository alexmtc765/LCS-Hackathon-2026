import streamlit as st

from pomodoro_app.state.session_state import get_active_task_data
from pomodoro_app.timer.controller import reset_timer


def render_active_task_panel() -> None:
    """Render selected task details and editable work/break plan fields."""
    active_task_data = get_active_task_data()
    if not active_task_data:
        return

    st.subheader(f"📝 {st.session_state.active_task}")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Work Minutes", active_task_data["total_work_minutes"])
    m2.metric("Breaks", active_task_data["number_of_breaks"])
    m3.metric("Total Break Minutes", active_task_data["total_break_minutes"])
    m4.metric(
        "Status",
        "✅ Done" if active_task_data["is_complete"] else "🔄 In Progress",
    )

    st.caption("Adjust this task plan (work and break distribution):")
    new_work = st.number_input(
        "Update Total Work Minutes",
        min_value=1,
        max_value=1440,
        value=int(active_task_data["total_work_minutes"]),
        step=1,
        key="edit_total_work_minutes",
    )
    new_breaks = st.number_input(
        "Update Number of Breaks",
        min_value=0,
        max_value=20,
        value=int(active_task_data["number_of_breaks"]),
        step=1,
        key="edit_number_of_breaks",
    )
    new_break_minutes = st.number_input(
        "Update Total Break Minutes",
        min_value=0,
        max_value=720,
        value=int(active_task_data["total_break_minutes"]),
        step=1,
        key="edit_total_break_minutes",
    )

    if st.button("Update Task Plan"):
        active_task_data["total_work_minutes"] = int(new_work)
        active_task_data["number_of_breaks"] = int(new_breaks)
        active_task_data["total_break_minutes"] = int(new_break_minutes)
        active_task_data["total_work_chunks"] = int(new_breaks) + 1
        active_task_data["completed_work_chunks"] = min(
            active_task_data["completed_work_chunks"],
            active_task_data["total_work_chunks"],
        )

        reset_timer()
        if active_task_data["completed_work_chunks"] < active_task_data["total_work_chunks"]:
            active_task_data["is_complete"] = False

        st.success("Task plan updated. Start again to run the new interval sequence.")
        st.rerun()

    st.divider()
