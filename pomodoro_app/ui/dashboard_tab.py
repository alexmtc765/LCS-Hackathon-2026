from collections import defaultdict
from datetime import date

import streamlit as st

from pomodoro_app.state.session_state import persist_data
from pomodoro_app.timer.controller import get_unlogged_work_minutes_today


def _today_work_minutes(session_logs: list[dict]) -> float:
    today_iso = date.today().isoformat()
    return sum(
        float(item.get("duration_minutes", 0.0))
        for item in session_logs
        if item.get("date") == today_iso and item.get("kind") == "work"
    )


def render_dashboard_tab() -> None:
    """Render daily goals, productivity summary, and historical session data."""
    st.subheader("Daily Productivity Dashboard")

    current_target = float(st.session_state.data["settings"].get("target_work_hours", 4.0))
    new_target = st.number_input(
        "Target Work Hours (Today)",
        min_value=0.5,
        max_value=24.0,
        value=current_target,
        step=0.5,
        key="dashboard_target_hours",
    )

    if float(new_target) != current_target:
        st.session_state.data["settings"]["target_work_hours"] = float(new_target)
        persist_data()

    logs = st.session_state.data.get("session_logs", [])
    completed_today_minutes = _today_work_minutes(logs)
    live_in_progress_minutes = get_unlogged_work_minutes_today()
    today_minutes = completed_today_minutes + live_in_progress_minutes
    target_minutes = float(new_target) * 60.0
    productivity_pct = (today_minutes / target_minutes * 100.0) if target_minutes > 0 else 0.0

    m1, m2, m3 = st.columns(3)
    m1.metric("Time Worked Today", f"{today_minutes:.1f} min")
    m2.metric("Target Work Time", f"{target_minutes:.1f} min")
    m3.metric("Productivity", f"{productivity_pct:.1f}%")
    if live_in_progress_minutes > 0:
        st.caption(
            f"Includes {live_in_progress_minutes:.1f} min currently in progress (not yet completed)."
        )

    by_day = defaultdict(float)
    for entry in logs:
        if entry.get("kind") == "work":
            by_day[str(entry.get("date", "unknown"))] += float(entry.get("duration_minutes", 0.0))

    st.markdown("### Work History by Day")
    if by_day:
        chart_data = {"minutes": by_day}
        st.bar_chart(chart_data)
    else:
        st.info("No completed work sessions logged yet.")

    st.markdown("### Session Calendar / History")
    if logs:
        rows = [
            {
                "Date": item.get("date", ""),
                "Time": item.get("time", ""),
                "Duration (min)": item.get("duration_minutes", 0.0),
                "Task Name": item.get("task_name", ""),
                "Kind": item.get("kind", ""),
            }
            for item in logs
        ]
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No history yet. Complete an interval to generate logs.")
