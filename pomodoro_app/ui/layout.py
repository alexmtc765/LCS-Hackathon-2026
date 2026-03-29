import streamlit as st

from pomodoro_app.ui.dashboard_tab import render_dashboard_tab
from pomodoro_app.ui.group_progress_panel import render_group_progress_panel
from pomodoro_app.ui.notifications import render_main_notifications
from pomodoro_app.ui.selectors import render_group_task_selectors
from pomodoro_app.ui.settings_panel import render_settings_sidebar, render_settings_tab
from pomodoro_app.ui.sidebar_management import render_task_management_tab
from pomodoro_app.ui.task_details_panel import render_active_task_panel
from pomodoro_app.ui.timer_panel import render_timer_panel


def render_app_layout() -> None:
    """Compose full page UI from independent section modules."""
    render_settings_sidebar()

    render_main_notifications()

    tab_timer, tab_tasks, tab_dashboard, tab_settings = st.tabs(
        ["Timer", "Task Management", "Dashboard", "Settings"]
    )

    with tab_timer:
        render_group_task_selectors()
        st.divider()
        render_timer_panel()
        st.divider()
        render_active_task_panel()
        render_group_progress_panel()

    with tab_tasks:
        render_task_management_tab()

    with tab_dashboard:
        render_dashboard_tab()

    with tab_settings:
        render_settings_tab()
