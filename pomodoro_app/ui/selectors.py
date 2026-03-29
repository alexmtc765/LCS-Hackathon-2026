import streamlit as st

from pomodoro_app.state.session_state import get_groups
from pomodoro_app.timer.controller import (
    persist_last_selected_task_context,
    reset_timer,
    restore_runtime_snapshot_for_task,
    save_current_runtime_snapshot,
)


def render_group_task_selectors() -> None:
    """Render active group/task selectors and reset timer on context switches."""
    groups = get_groups()
    col_group, col_task = st.columns(2)

    with col_group:
        group_options = list(groups.keys())
        if group_options:
            group_index = (
                group_options.index(st.session_state.active_group)
                if st.session_state.active_group in group_options
                else 0
            )
            selected_group = st.selectbox(
                "📁 Active Group",
                options=group_options,
                index=group_index,
                key="active_group_select",
            )
            if selected_group != st.session_state.active_group:
                save_current_runtime_snapshot()
                st.session_state.active_group = selected_group
                st.session_state.active_task = None
                reset_timer()
                persist_last_selected_task_context()
                st.rerun()
            else:
                st.session_state.active_group = selected_group
        else:
            st.info("Create a group in the sidebar to get started.")
            selected_group = None

    with col_task:
        if selected_group and groups.get(selected_group):
            task_options = list(groups[selected_group]["tasks"].keys())
            if task_options:
                task_index = (
                    task_options.index(st.session_state.active_task)
                    if st.session_state.active_task in task_options
                    else 0
                )
                selected_task = st.selectbox(
                    "📝 Active Task",
                    options=task_options,
                    index=task_index,
                    key="active_task_select",
                )
                if selected_task != st.session_state.active_task:
                    save_current_runtime_snapshot()
                    st.session_state.active_task = selected_task
                    restored = restore_runtime_snapshot_for_task(
                        (st.session_state.active_group, selected_task)
                    )
                    if not restored:
                        reset_timer()
                    persist_last_selected_task_context()
                    st.rerun()
                else:
                    st.session_state.active_task = selected_task
                    persist_last_selected_task_context()
            else:
                st.info("Add a task to this group first.")
