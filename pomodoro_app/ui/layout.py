import streamlit as st

from pomodoro_app.ui.group_progress_panel import render_group_progress_panel
from pomodoro_app.ui.notifications import render_main_notifications
from pomodoro_app.ui.selectors import render_group_task_selectors
from pomodoro_app.ui.sidebar_management import render_sidebar_group_and_task_management
from pomodoro_app.ui.task_details_panel import render_active_task_panel
from pomodoro_app.ui.timer_panel import render_timer_panel


def render_app_layout() -> None:
    """Compose full page UI from independent section modules."""
    render_sidebar_group_and_task_management()

    render_main_notifications()
    render_group_task_selectors()

    st.divider()
    render_timer_panel()

    st.divider()
    render_active_task_panel()
    render_group_progress_panel()
