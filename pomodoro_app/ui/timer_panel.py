import streamlit as st

from pomodoro_app.state.session_state import active_task_key, get_active_task_data, persist_data
from pomodoro_app.timer.controller import (
    get_remaining_seconds,
    pause_timer,
    reset_timer,
    resume_queue,
    skip_to_next_interval,
    start_new_queue_for_active_task,
)
from pomodoro_app.timer.intervals import build_interval_queue, format_seconds


def render_timer_panel() -> None:
    """Render timer metric, queue preview, and core timer controls."""
    active_task_data = get_active_task_data()

    timer_placeholder = st.empty()
    remaining_secs = get_remaining_seconds()

    if st.session_state.current_interval_label:
        interval_label = st.session_state.current_interval_label
    elif active_task_data:
        interval_label = "Ready"
    else:
        interval_label = "No Task Selected"

    timer_placeholder.metric(
        label=f"⏱ Time Remaining ({interval_label})",
        value=format_seconds(remaining_secs),
    )

    if active_task_data and not st.session_state.interval_queue:
        planned_queue = build_interval_queue(active_task_data)
        preview = " → ".join(
            f"{item['label']} ({format_seconds(item['seconds'])})" for item in planned_queue
        )
        st.caption(f"Planned sequence: {preview}")

    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
    task_is_complete = bool(active_task_data and active_task_data["is_complete"])

    current_key = active_task_key()
    can_resume = (
        bool(st.session_state.interval_queue)
        and not st.session_state.timer_running
        and st.session_state.current_task_key == current_key
    )

    with btn_col1:
        if st.session_state.timer_running:
            if st.button("⏸ Pause", use_container_width=True):
                pause_timer()
                st.rerun()
        else:
            start_label = "▶ Resume Interval" if can_resume else "▶ Start Task Plan"
            start_disabled = active_task_data is None or task_is_complete
            if st.button(
                start_label,
                disabled=start_disabled,
                use_container_width=True,
                type="primary",
            ):
                if can_resume:
                    resume_queue()
                else:
                    start_new_queue_for_active_task()
                st.rerun()

    with btn_col2:
        if st.button("🔄 Reset Timer", use_container_width=True):
            reset_timer()
            st.rerun()

    with btn_col3:
        skip_disabled = (
            active_task_data is None
            or task_is_complete
            or not st.session_state.interval_queue
            or st.session_state.current_task_key != current_key
        )
        if st.button("⏭ Skip To Next", disabled=skip_disabled, use_container_width=True):
            skip_to_next_interval()
            st.rerun()

    with btn_col4:
        if active_task_data:
            if not task_is_complete:
                if st.button("✅ Mark Task Complete", use_container_width=True):
                    active_task_data["is_complete"] = True
                    persist_data()
                    reset_timer()
                    st.rerun()
            else:
                if st.button("↩ Reopen Task", use_container_width=True):
                    active_task_data["is_complete"] = False
                    persist_data()
                    st.rerun()
