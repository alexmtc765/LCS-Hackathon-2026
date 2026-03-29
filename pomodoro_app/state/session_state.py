import streamlit as st

from pomodoro_app.storage.json_store import load_data, save_data


def init_state() -> None:
    """Initialize runtime state and hydrated persisted data."""
    if "data" not in st.session_state:
        st.session_state.data = load_data()

    runtime_state = st.session_state.data.get("runtime_state", {})

    if "active_group" not in st.session_state:
        st.session_state.active_group = runtime_state.get("last_selected_group")

    if "active_task" not in st.session_state:
        st.session_state.active_task = runtime_state.get("last_selected_task")

    if "timer_running" not in st.session_state:
        st.session_state.timer_running = False

    if "timer_start_time" not in st.session_state:
        st.session_state.timer_start_time = None

    if "timer_remaining_at_start" not in st.session_state:
        st.session_state.timer_remaining_at_start = 0.0

    if "interval_queue" not in st.session_state:
        st.session_state.interval_queue = []

    if "current_interval_index" not in st.session_state:
        st.session_state.current_interval_index = 0

    if "current_interval_kind" not in st.session_state:
        st.session_state.current_interval_kind = ""

    if "current_interval_label" not in st.session_state:
        st.session_state.current_interval_label = ""

    if "current_task_key" not in st.session_state:
        st.session_state.current_task_key = None

    if "session_just_completed" not in st.session_state:
        st.session_state.session_just_completed = False

    if "interval_transition_message" not in st.session_state:
        st.session_state.interval_transition_message = ""

    if "pending_sound_event" not in st.session_state:
        st.session_state.pending_sound_event = ""


def get_groups() -> dict:
    """Return persisted groups dictionary."""
    return st.session_state.data["groups"]


def persist_data() -> None:
    """Save current in-memory data snapshot to disk."""
    save_data(st.session_state.data)


def active_task_key() -> tuple[str, str] | None:
    """Return selected task as a stable (group, task) tuple."""
    group_name = st.session_state.active_group
    task_name = st.session_state.active_task
    if group_name and task_name:
        return group_name, task_name
    return None


def get_active_task_data() -> dict | None:
    """Resolve selected task dict from nested groups state."""
    key = active_task_key()
    if not key:
        return None

    group_name, task_name = key
    group = get_groups().get(group_name)
    if not group:
        return None

    return group["tasks"].get(task_name)
