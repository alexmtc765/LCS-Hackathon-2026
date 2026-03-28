import time
import streamlit as st

from pomodoro_app.state.session_state import active_task_key, get_active_task_data
from pomodoro_app.timer.intervals import build_interval_queue


def get_remaining_seconds() -> float:
    """Compute remaining seconds for current interval."""
    if not st.session_state.timer_running:
        return st.session_state.timer_remaining_at_start

    elapsed = time.time() - st.session_state.timer_start_time
    remaining = st.session_state.timer_remaining_at_start - elapsed
    return max(0.0, remaining)


def sync_interval_metadata() -> None:
    """Sync current interval label/kind from queue and index."""
    queue = st.session_state.interval_queue
    idx = st.session_state.current_interval_index

    if queue and 0 <= idx < len(queue):
        st.session_state.current_interval_kind = queue[idx]["kind"]
        st.session_state.current_interval_label = queue[idx]["label"]
    else:
        st.session_state.current_interval_kind = ""
        st.session_state.current_interval_label = ""


def reset_timer() -> None:
    """Clear all runtime queue/timer state for current run."""
    st.session_state.timer_running = False
    st.session_state.timer_start_time = None
    st.session_state.timer_remaining_at_start = 0.0
    st.session_state.interval_queue = []
    st.session_state.current_interval_index = 0
    st.session_state.current_interval_kind = ""
    st.session_state.current_interval_label = ""
    st.session_state.current_task_key = None
    st.session_state.interval_transition_message = ""
    st.session_state.session_just_completed = False


def pause_timer() -> None:
    """Pause countdown and preserve current interval remaining time."""
    if st.session_state.timer_running:
        st.session_state.timer_remaining_at_start = get_remaining_seconds()
        st.session_state.timer_running = False
        st.session_state.timer_start_time = None


def resume_queue() -> None:
    """Resume existing queue countdown from paused seconds."""
    if st.session_state.interval_queue and st.session_state.timer_remaining_at_start > 0:
        st.session_state.timer_running = True
        st.session_state.timer_start_time = time.time()


def start_new_queue_for_active_task() -> None:
    """Build and start a fresh work/break queue for selected task."""
    task = get_active_task_data()
    task_key = active_task_key()
    if not task or not task_key:
        return

    queue = build_interval_queue(task)
    if not queue:
        return

    task["completed_work_chunks"] = 0
    task["total_work_chunks"] = int(task["number_of_breaks"]) + 1
    task["is_complete"] = False

    st.session_state.interval_queue = queue
    st.session_state.current_interval_index = 0
    st.session_state.current_task_key = task_key

    first_interval = queue[0]
    st.session_state.timer_remaining_at_start = float(first_interval["seconds"])
    st.session_state.timer_start_time = time.time()
    st.session_state.timer_running = True

    sync_interval_metadata()
    st.session_state.session_just_completed = False
    st.session_state.interval_transition_message = f"Starting {first_interval['label']}"


def advance_interval_or_finish() -> None:
    """
    End current interval and transition to next one, or finish task.

    Final work chunk completion marks task complete and triggers celebration.
    """
    queue = st.session_state.interval_queue
    idx = st.session_state.current_interval_index

    if not queue or not (0 <= idx < len(queue)):
        reset_timer()
        return

    current = queue[idx]
    task = get_active_task_data()

    if current["kind"] == "work" and task:
        task["completed_work_chunks"] = min(
            task["completed_work_chunks"] + 1,
            task["total_work_chunks"],
        )

    is_last_interval = idx == len(queue) - 1
    if is_last_interval:
        if task:
            task["is_complete"] = True
        reset_timer()
        st.session_state.session_just_completed = True
        return

    next_idx = idx + 1
    next_interval = queue[next_idx]

    st.session_state.current_interval_index = next_idx
    st.session_state.timer_remaining_at_start = float(next_interval["seconds"])
    st.session_state.timer_start_time = time.time()
    st.session_state.timer_running = True
    sync_interval_metadata()

    if next_interval["kind"] == "break":
        st.session_state.interval_transition_message = (
            f"Work chunk finished. {next_interval['label']} is starting."
        )
    else:
        st.session_state.interval_transition_message = (
            f"Break finished. {next_interval['label']} is starting."
        )


def process_timer_zero_crossing() -> None:
    """Advance queue immediately when countdown reaches 00:00."""
    if st.session_state.timer_running and get_remaining_seconds() <= 0:
        advance_interval_or_finish()


def run_timer_tick() -> None:
    """Drive live countdown by rerunning once per second while running."""
    if st.session_state.timer_running:
        time.sleep(1)
        st.rerun()
