import time
from datetime import date, datetime

import streamlit as st

from pomodoro_app.state.session_state import (
    active_task_key,
    get_active_task_data,
    persist_data,
)
from pomodoro_app.timer.intervals import build_interval_queue


def _task_run_key(task_key: tuple[str, str]) -> str:
    """Build a stable string key for persisted per-task runtime snapshots."""
    group_name, task_name = task_key
    return f"{group_name} :: {task_name}"


def _get_task_runs_map() -> dict:
    """Return persisted runtime snapshots map from data root."""
    return st.session_state.data["runtime_state"]["task_runs"]


def save_current_runtime_snapshot() -> None:
    """
    Persist current task runtime so progress survives refresh and task switching.

    Snapshot contains queue, position, and remaining seconds for the active task.
    """
    task_key = st.session_state.current_task_key
    queue = st.session_state.interval_queue
    if not task_key or not queue:
        return

    key = _task_run_key(task_key)
    remaining_seconds = get_remaining_seconds()
    _get_task_runs_map()[key] = {
        "interval_queue": queue,
        "current_interval_index": st.session_state.current_interval_index,
        "remaining_seconds": float(remaining_seconds),
        "timer_running": bool(st.session_state.timer_running),
        "updated_at": datetime.now().isoformat(),
    }
    persist_data()


def clear_runtime_snapshot_for_task(task_key: tuple[str, str] | None) -> None:
    """Delete persisted runtime snapshot for a task when run is reset/finished."""
    if not task_key:
        return
    _get_task_runs_map().pop(_task_run_key(task_key), None)
    persist_data()


def restore_runtime_snapshot_for_task(task_key: tuple[str, str] | None) -> bool:
    """Load saved queue state for task into session runtime, if available."""
    if not task_key:
        return False

    snapshot = _get_task_runs_map().get(_task_run_key(task_key))
    if not snapshot:
        return False

    queue = snapshot.get("interval_queue", [])
    idx = int(snapshot.get("current_interval_index", 0))
    if not queue or not (0 <= idx < len(queue)):
        clear_runtime_snapshot_for_task(task_key)
        return False

    st.session_state.interval_queue = queue
    st.session_state.current_interval_index = idx
    st.session_state.current_task_key = task_key
    st.session_state.timer_remaining_at_start = float(snapshot.get("remaining_seconds", 0.0))
    st.session_state.timer_running = bool(snapshot.get("timer_running", False))
    st.session_state.timer_start_time = time.time() if st.session_state.timer_running else None
    sync_interval_metadata()
    return True


def persist_last_selected_task_context() -> None:
    """Persist selected group/task so refresh restores user's current context."""
    st.session_state.data["runtime_state"]["last_selected_group"] = st.session_state.active_group
    st.session_state.data["runtime_state"]["last_selected_task"] = st.session_state.active_task
    persist_data()


def _append_session_log(duration_minutes: float, task_name: str, kind: str) -> None:
    """Store timestamped interval completion in persistent history."""
    now = datetime.now()
    st.session_state.data["session_logs"].append(
        {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "duration_minutes": round(duration_minutes, 2),
            "task_name": task_name,
            "kind": kind,
        }
    )


def _add_task_time_totals(group_name: str, task_name: str, minutes: float) -> None:
    """Accumulate total tracked minutes for each task in persistent storage."""
    task_key = f"{group_name} :: {task_name}"
    current = float(st.session_state.data["task_totals"].get(task_key, 0.0))
    st.session_state.data["task_totals"][task_key] = round(current + minutes, 2)


def _resolve_task_identity() -> tuple[str, str, dict | None]:
    """Return (group_name, task_name, task_data) for current active task context."""
    task = get_active_task_data()
    task_key = active_task_key()
    if task_key:
        group_name, task_name = task_key
    else:
        group_name, task_name = "", ""
    return group_name, task_name, task


def _elapsed_minutes_for_current_interval(current: dict, assume_full: bool) -> float:
    """Compute elapsed minutes in current interval (full or partial)."""
    if assume_full:
        elapsed_seconds = float(current["seconds"])
    else:
        remaining = (
            get_remaining_seconds()
            if st.session_state.timer_running
            else float(st.session_state.timer_remaining_at_start)
        )
        elapsed_seconds = max(0.0, float(current["seconds"]) - remaining)
        elapsed_seconds = min(elapsed_seconds, float(current["seconds"]))

    return float(elapsed_seconds) / 60.0


def _record_interval_progress(
    current: dict,
    task: dict | None,
    group_name: str,
    task_name: str,
    elapsed_minutes: float,
) -> None:
    """Apply elapsed interval time to logs/totals and task progress counters."""
    interval_kind = current["kind"]

    if task_name and elapsed_minutes > 0:
        _append_session_log(elapsed_minutes, task_name, interval_kind)

    if interval_kind == "work" and task:
        task["completed_work_chunks"] = min(
            task["completed_work_chunks"] + 1,
            task["total_work_chunks"],
        )
        if elapsed_minutes > 0:
            task["total_time_minutes_spent"] = round(
                float(task.get("total_time_minutes_spent", 0.0)) + elapsed_minutes,
                2,
            )
            _add_task_time_totals(group_name, task_name, elapsed_minutes)


def get_unlogged_work_minutes_today() -> float:
    """
    Return live in-progress work minutes not yet written as completed session logs.

    This includes saved runtime snapshots (paused or running) updated today.
    """
    today_iso = date.today().isoformat()
    total_minutes = 0.0

    for key, snapshot in _get_task_runs_map().items():
        updated_at = str(snapshot.get("updated_at", ""))
        if not updated_at.startswith(today_iso):
            continue

        queue = snapshot.get("interval_queue", [])
        idx = int(snapshot.get("current_interval_index", 0))
        if not queue or not (0 <= idx < len(queue)):
            continue

        current = queue[idx]
        if current.get("kind") != "work":
            continue

        remaining = float(snapshot.get("remaining_seconds", 0.0))

        # For currently running active task, use precise live remaining seconds.
        current_key = st.session_state.current_task_key
        if current_key and _task_run_key(current_key) == key and st.session_state.timer_running:
            remaining = get_remaining_seconds()

        elapsed_seconds = max(0.0, float(current.get("seconds", 0.0)) - remaining)
        elapsed_seconds = min(elapsed_seconds, float(current.get("seconds", 0.0)))
        total_minutes += elapsed_seconds / 60.0

    return round(total_minutes, 2)


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
    clear_runtime_snapshot_for_task(st.session_state.current_task_key)
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
        save_current_runtime_snapshot()


def resume_queue() -> None:
    """Resume existing queue countdown from paused seconds."""
    if st.session_state.interval_queue and st.session_state.timer_remaining_at_start > 0:
        st.session_state.timer_running = True
        st.session_state.timer_start_time = time.time()
        save_current_runtime_snapshot()


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
    save_current_runtime_snapshot()
    persist_data()


def advance_interval_or_finish() -> None:
    """
    End current interval and transition to next one, or finish task.

    Final work chunk completion marks task complete and triggers celebration.
    Uses a 10s transition phase with appropriate sounds:
    - Work ends -> Break starts: play relaxing sound
    - Break ends -> Work starts: play harsh sound
    - Task ends: play relaxing sound
    """
    queue = st.session_state.interval_queue
    idx = st.session_state.current_interval_index

    if not queue or not (0 <= idx < len(queue)):
        reset_timer()
        return

    current = queue[idx]
    group_name, task_name, task = _resolve_task_identity()
    elapsed_minutes = _elapsed_minutes_for_current_interval(current, assume_full=True)
    _record_interval_progress(current, task, group_name, task_name, elapsed_minutes)

    is_last_interval = idx == len(queue) - 1
    if is_last_interval:
        if task:
            task["is_complete"] = True
        clear_runtime_snapshot_for_task(st.session_state.current_task_key)
        reset_timer()
        st.session_state.session_just_completed = True
        # Task ends: play relaxing sound for 10s
        st.session_state.pending_sound_event = "task_end"
        st.session_state.pending_sound_tone = "Relaxing"
        return

    next_idx = idx + 1
    next_interval = queue[next_idx]

    # Enter 10s transition phase with appropriate sound
    st.session_state.transition_phase = True
    st.session_state.transition_target_index = next_idx
    st.session_state.transition_sound_active = True
    st.session_state.timer_remaining_at_start = 10.0
    st.session_state.timer_start_time = time.time()
    st.session_state.timer_running = True

    if next_interval["kind"] == "break":
        # Work ends -> Break starts: play relaxing sound
        st.session_state.transition_sound_event = "work_end"
        st.session_state.transition_sound_tone = "Relaxing"
        st.session_state.pending_sound_tone = "Relaxing"
        st.session_state.interval_transition_message = (
            f"Work chunk finished. {next_interval['label']} starting in 10s."
        )
    else:
        # Break ends -> Work starts: play harsh sound
        st.session_state.transition_sound_event = "break_end"
        st.session_state.transition_sound_tone = "Harsh"
        st.session_state.pending_sound_tone = "Harsh"
        st.session_state.interval_transition_message = (
            f"Break finished. {next_interval['label']} starting in 10s."
        )

    st.session_state.pending_sound_event = st.session_state.transition_sound_event
    save_current_runtime_snapshot()
    persist_data()


def skip_to_next_interval() -> None:
    """Skip the current interval and jump to the next queued interval."""
    queue = st.session_state.interval_queue
    idx = st.session_state.current_interval_index

    if not queue or not (0 <= idx < len(queue)):
        return

    current = queue[idx]
    group_name, task_name, task = _resolve_task_identity()
    elapsed_minutes = _elapsed_minutes_for_current_interval(current, assume_full=False)
    _record_interval_progress(current, task, group_name, task_name, elapsed_minutes)

    if idx >= len(queue) - 1:
        if task:
            task["is_complete"] = True
        clear_runtime_snapshot_for_task(st.session_state.current_task_key)
        reset_timer()
        st.session_state.session_just_completed = True
        # Task ends: play relaxing sound for 10s
        st.session_state.pending_sound_event = "task_end"
        st.session_state.pending_sound_tone = "Relaxing"
        persist_data()
        return

    next_idx = idx + 1
    next_interval = queue[next_idx]

    # Enter 10s transition phase with appropriate sound
    st.session_state.transition_phase = True
    st.session_state.transition_target_index = next_idx
    st.session_state.transition_sound_active = True
    st.session_state.timer_remaining_at_start = 10.0
    st.session_state.timer_start_time = time.time()
    st.session_state.timer_running = True

    if next_interval["kind"] == "break":
        # Work ends -> Break starts: play relaxing sound
        st.session_state.transition_sound_event = "work_end"
        st.session_state.transition_sound_tone = "Relaxing"
        st.session_state.pending_sound_tone = "Relaxing"
        st.session_state.interval_transition_message = (
            f"Skipped: {next_interval['label']} starting in 10s."
        )
    else:
        # Break ends -> Work starts: play harsh sound
        st.session_state.transition_sound_event = "break_end"
        st.session_state.transition_sound_tone = "Harsh"
        st.session_state.pending_sound_tone = "Harsh"
        st.session_state.interval_transition_message = (
            f"Skipped: {next_interval['label']} starting in 10s."
        )

    st.session_state.pending_sound_event = st.session_state.transition_sound_event
    save_current_runtime_snapshot()
    persist_data()


def process_timer_zero_crossing() -> None:
    """Advance queue immediately when countdown reaches 00:00."""
    if st.session_state.timer_running and get_remaining_seconds() <= 0:
        # If we're in a transition phase, finalize the transition and actually
        # start the queued interval now.
        if st.session_state.get("transition_phase"):
            target = st.session_state.get("transition_target_index")
            queue = st.session_state.interval_queue
            if queue and target is not None and 0 <= target < len(queue):
                st.session_state.current_interval_index = int(target)
                next_interval = queue[st.session_state.current_interval_index]
                st.session_state.timer_remaining_at_start = float(next_interval["seconds"])
                st.session_state.timer_start_time = time.time()
                st.session_state.timer_running = True
                st.session_state.transition_phase = False
                st.session_state.transition_target_index = None
                st.session_state.transition_sound_event = ""
                st.session_state.transition_sound_active = False
                st.session_state.pending_sound_event = ""
                st.session_state.pending_sound_tone = ""
                st.session_state.interval_transition_message = f"Starting {next_interval['label']}"
                sync_interval_metadata()
                save_current_runtime_snapshot()
                persist_data()
                return
            else:
                # Malformed transition state; reset to safe defaults.
                st.session_state.transition_phase = False
                st.session_state.transition_target_index = None
                st.session_state.transition_sound_event = ""
                st.session_state.transition_sound_active = False
                reset_timer()
                return

        # Normal non-transition boundary behavior.
        advance_interval_or_finish()


def run_timer_tick() -> None:
    """Drive live countdown by rerunning once per second while running."""
    if st.session_state.timer_running:
        # Snapshot every tick so refresh restores near-real-time progress.
        save_current_runtime_snapshot()

        # If we're in the brief transition phase, repeatedly set the pending
        # sound event so the audio keeps playing across reruns for the full
        # transition duration (approx. 10 seconds). This will trigger the
        # front-end audio player on each rerun.
        if st.session_state.get("transition_phase") and st.session_state.get("transition_sound_event"):
            st.session_state.pending_sound_event = st.session_state.transition_sound_event
            st.session_state.pending_sound_tone = st.session_state.get("transition_sound_tone", "")

        time.sleep(1)
        st.rerun()
