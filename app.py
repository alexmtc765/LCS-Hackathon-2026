"""
app.py — Dynamic Work/Break Timer with Task Group Tracking
===========================================================
A single-file Streamlit prototype. All data lives in st.session_state
(no database, no file I/O) and is lost when the browser tab is closed.

Run with:
    streamlit run app.py
"""

import time
import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be the very first Streamlit call in the script)
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="🍅 Pomodoro Tracker",
    page_icon="🍅",
    layout="wide",
)

# ──────────────────────────────────────────────────────────────────────────────
# SESSION STATE INITIALISATION
# ──────────────────────────────────────────────────────────────────────────────
#
# Streamlit reruns this full script whenever a widget changes, so every key we
# depend on is initialized once and then reused.
#
# Root data structure in st.session_state.groups:
#
#   {
#       "Math": {
#           "tasks": {
#               "Vectors 1.1": {
#                   "total_work_minutes": 60,
#                   "number_of_breaks": 1,
#                   "total_break_minutes": 10,
#                   "total_work_chunks": 2,
#                   "completed_work_chunks": 0,
#                   "is_complete": False,
#               }
#           }
#       }
#   }
#
# Timer queue shape in st.session_state.interval_queue:
#   [
#       {"kind": "work",  "seconds": 1800.0, "label": "Work 1/2"},
#       {"kind": "break", "seconds":  600.0, "label": "Break 1/1"},
#       {"kind": "work",  "seconds": 1800.0, "label": "Work 2/2"},
#   ]
#
# ──────────────────────────────────────────────────────────────────────────────


def _init_state() -> None:
    """Set default values for every session-state key we rely on."""

    if "groups" not in st.session_state:
        st.session_state.groups = {}

    if "active_group" not in st.session_state:
        st.session_state.active_group = None

    if "active_task" not in st.session_state:
        st.session_state.active_task = None

    # Timer state for the currently selected task queue.
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

    # Stores (group_name, task_name) so paused queues are tied to one task.
    if "current_task_key" not in st.session_state:
        st.session_state.current_task_key = None

    # One-shot flags/messages for UI feedback.
    if "session_just_completed" not in st.session_state:
        st.session_state.session_just_completed = False

    if "interval_transition_message" not in st.session_state:
        st.session_state.interval_transition_message = ""


_init_state()


# ──────────────────────────────────────────────────────────────────────────────
# TIMER + QUEUE HELPERS
# ──────────────────────────────────────────────────────────────────────────────


def _active_task_key() -> tuple[str, str] | None:
    """Return a stable key for the selected task, or None if incomplete."""
    g = st.session_state.active_group
    t = st.session_state.active_task
    if g and t:
        return g, t
    return None


def get_active_task_data() -> dict | None:
    """Resolve and return the selected task dict from session state."""
    key = _active_task_key()
    if not key:
        return None
    group_name, task_name = key
    group = st.session_state.groups.get(group_name)
    if not group:
        return None
    return group["tasks"].get(task_name)


def get_remaining_seconds() -> float:
    """
    Calculate seconds left in the active interval.

    If paused, return the saved number of seconds.
    If running, subtract elapsed wall-clock time from the saved start value.
    """
    if not st.session_state.timer_running:
        return st.session_state.timer_remaining_at_start

    elapsed = time.time() - st.session_state.timer_start_time
    remaining = st.session_state.timer_remaining_at_start - elapsed
    return max(0.0, remaining)


def fmt(seconds: float) -> str:
    """Format seconds as MM:SS (for example 07:04)."""
    s = max(0, int(seconds))
    return f"{s // 60:02d}:{s % 60:02d}"


def build_interval_queue(task: dict) -> list[dict]:
    """
    Build a full work/break sequence from task settings.

    Rules:
    - If breaks == 0: one continuous work interval.
    - If breaks == N > 0:
      - Work is split into N + 1 equal chunks.
      - Total break time is split into N equal chunks.
      - Sequence alternates work -> break -> work -> ... -> work.
    """
    total_work_minutes = float(task["total_work_minutes"])
    number_of_breaks = int(task["number_of_breaks"])
    total_break_minutes = float(task["total_break_minutes"])

    total_work_seconds = total_work_minutes * 60.0
    total_break_seconds = total_break_minutes * 60.0

    if number_of_breaks == 0:
        return [
            {
                "kind": "work",
                "seconds": total_work_seconds,
                "label": "Work 1/1",
            }
        ]

    total_work_chunks = number_of_breaks + 1
    work_chunk_seconds = total_work_seconds / total_work_chunks
    break_chunk_seconds = total_break_seconds / number_of_breaks

    queue: list[dict] = []
    for idx in range(total_work_chunks):
        queue.append(
            {
                "kind": "work",
                "seconds": work_chunk_seconds,
                "label": f"Work {idx + 1}/{total_work_chunks}",
            }
        )
        if idx < number_of_breaks:
            queue.append(
                {
                    "kind": "break",
                    "seconds": break_chunk_seconds,
                    "label": f"Break {idx + 1}/{number_of_breaks}",
                }
            )

    return queue


def _sync_interval_metadata() -> None:
    """Refresh current interval label/kind from queue + index."""
    q = st.session_state.interval_queue
    i = st.session_state.current_interval_index
    if q and 0 <= i < len(q):
        st.session_state.current_interval_kind = q[i]["kind"]
        st.session_state.current_interval_label = q[i]["label"]
    else:
        st.session_state.current_interval_kind = ""
        st.session_state.current_interval_label = ""


def _start_new_queue_for_active_task() -> None:
    """Create and start a fresh queue from the selected task settings."""
    task = get_active_task_data()
    task_key = _active_task_key()
    if not task or not task_key:
        return

    queue = build_interval_queue(task)
    if not queue:
        return

    # A fresh run starts work-chunk progress from zero for this task plan.
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

    _sync_interval_metadata()
    st.session_state.session_just_completed = False
    st.session_state.interval_transition_message = f"Starting {first_interval['label']}"


def _resume_queue() -> None:
    """Resume countdown from saved remaining seconds in the same interval."""
    if st.session_state.interval_queue and st.session_state.timer_remaining_at_start > 0:
        st.session_state.timer_running = True
        st.session_state.timer_start_time = time.time()


def _pause_timer() -> None:
    """Pause countdown while preserving seconds left in this interval."""
    if st.session_state.timer_running:
        st.session_state.timer_remaining_at_start = get_remaining_seconds()
        st.session_state.timer_running = False
        st.session_state.timer_start_time = None


def _reset_timer() -> None:
    """Clear timer runtime state and interval queue for the current run."""
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


def _advance_interval_or_finish() -> None:
    """
    Handle end-of-interval behavior for queue mode.

    - Finishing a work chunk increments completed_work_chunks.
    - If this was the final work chunk, mark task complete + balloons.
    - Otherwise move to the next interval and immediately start it.
    """
    queue = st.session_state.interval_queue
    idx = st.session_state.current_interval_index

    if not queue or not (0 <= idx < len(queue)):
        _reset_timer()
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
        _reset_timer()
        st.session_state.session_just_completed = True
        return

    next_idx = idx + 1
    next_interval = queue[next_idx]

    st.session_state.current_interval_index = next_idx
    st.session_state.timer_remaining_at_start = float(next_interval["seconds"])
    st.session_state.timer_start_time = time.time()
    st.session_state.timer_running = True
    _sync_interval_metadata()

    if next_interval["kind"] == "break":
        st.session_state.interval_transition_message = (
            f"Work chunk finished. {next_interval['label']} is starting."
        )
    else:
        st.session_state.interval_transition_message = (
            f"Break finished. {next_interval['label']} is starting."
        )


# ──────────────────────────────────────────────────────────────────────────────
# ZERO-CROSSING CHECK  (runs before any UI is rendered)
# ──────────────────────────────────────────────────────────────────────────────

if st.session_state.timer_running and get_remaining_seconds() <= 0:
    _advance_interval_or_finish()


# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR — GROUP & TASK MANAGEMENT
# ──────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("📋 Groups & Tasks")

    st.subheader("➕ New Group")
    new_group_name = st.text_input(
        "Group name",
        placeholder="e.g. Math, Writing, Coding",
        key="new_group_input",
    )
    if st.button("Create Group", use_container_width=True):
        name = new_group_name.strip()
        if not name:
            st.warning("Please enter a group name.")
        elif name in st.session_state.groups:
            st.warning(f'"{name}" already exists.')
        else:
            st.session_state.groups[name] = {"tasks": {}}
            st.success(f'Group "{name}" created!')
            st.rerun()

    st.divider()

    st.subheader("➕ New Task")
    if st.session_state.groups:
        group_for_task = st.selectbox(
            "Add task to group",
            options=list(st.session_state.groups.keys()),
            key="group_for_task_select",
        )
        new_task_name = st.text_input(
            "Task name",
            placeholder="e.g. Vectors 1.1",
            key="new_task_input",
        )
        total_work_minutes_input = st.number_input(
            "Total Work Minutes",
            min_value=1,
            max_value=1440,
            value=60,
            step=1,
            key="task_total_work_minutes",
        )
        number_of_breaks_input = st.number_input(
            "Number of Breaks",
            min_value=0,
            max_value=20,
            value=1,
            step=1,
            key="task_number_of_breaks",
        )
        total_break_minutes_input = st.number_input(
            "Total Break Minutes",
            min_value=0,
            max_value=720,
            value=10,
            step=1,
            key="task_total_break_minutes",
        )

        if number_of_breaks_input == 0 and total_break_minutes_input > 0:
            st.caption(
                "Breaks are set to 0, so total break minutes will be ignored for this task."
            )

        if st.button("Add Task", use_container_width=True):
            task_name = new_task_name.strip()
            if not task_name:
                st.warning("Please enter a task name.")
            elif task_name in st.session_state.groups[group_for_task]["tasks"]:
                st.warning(f'"{task_name}" already exists in "{group_for_task}".')
            else:
                total_work_chunks = int(number_of_breaks_input) + 1
                st.session_state.groups[group_for_task]["tasks"][task_name] = {
                    "total_work_minutes": int(total_work_minutes_input),
                    "number_of_breaks": int(number_of_breaks_input),
                    "total_break_minutes": int(total_break_minutes_input),
                    "total_work_chunks": total_work_chunks,
                    "completed_work_chunks": 0,
                    "is_complete": False,
                }
                st.success(f'"{task_name}" added to "{group_for_task}"!')
                st.rerun()
    else:
        st.info("Create a group first.")

    st.divider()

    st.subheader("📊 Overview")
    if not st.session_state.groups:
        st.caption("No groups yet.")
    else:
        for g_name, g_data in st.session_state.groups.items():
            with st.expander(f"📁 {g_name}"):
                if not g_data["tasks"]:
                    st.caption("No tasks yet.")
                else:
                    for t_name, t_data in g_data["tasks"].items():
                        icon = "✅" if t_data["is_complete"] else "🔄"
                        st.caption(
                            f"{icon} **{t_name}** — "
                            f"{t_data['completed_work_chunks']}/{t_data['total_work_chunks']} work chunks"
                        )
                        st.caption(
                            f"{t_data['total_work_minutes']}m work | "
                            f"{t_data['number_of_breaks']} breaks | "
                            f"{t_data['total_break_minutes']}m total break"
                        )


# ──────────────────────────────────────────────────────────────────────────────
# MAIN AREA
# ──────────────────────────────────────────────────────────────────────────────

st.title("🍅 Pomodoro Timer")

if st.session_state.interval_transition_message:
    st.info(st.session_state.interval_transition_message)
    st.session_state.interval_transition_message = ""

if st.session_state.session_just_completed:
    st.balloons()
    st.success("🎉 Final work chunk complete. Task marked complete.")
    st.session_state.session_just_completed = False

col_g, col_t = st.columns(2)

with col_g:
    group_options = list(st.session_state.groups.keys())
    if group_options:
        g_idx = (
            group_options.index(st.session_state.active_group)
            if st.session_state.active_group in group_options
            else 0
        )
        selected_group = st.selectbox(
            "📁 Active Group",
            options=group_options,
            index=g_idx,
            key="active_group_select",
        )
        if selected_group != st.session_state.active_group:
            st.session_state.active_group = selected_group
            st.session_state.active_task = None
            _reset_timer()
            st.rerun()
        else:
            st.session_state.active_group = selected_group
    else:
        st.info("Create a group in the sidebar to get started.")
        selected_group = None

with col_t:
    if selected_group and st.session_state.groups.get(selected_group):
        task_options = list(st.session_state.groups[selected_group]["tasks"].keys())
        if task_options:
            t_idx = (
                task_options.index(st.session_state.active_task)
                if st.session_state.active_task in task_options
                else 0
            )
            selected_task = st.selectbox(
                "📝 Active Task",
                options=task_options,
                index=t_idx,
                key="active_task_select",
            )
            if selected_task != st.session_state.active_task:
                st.session_state.active_task = selected_task
                _reset_timer()
                st.rerun()
            else:
                st.session_state.active_task = selected_task
        else:
            st.info("Add a task to this group first.")
            selected_task = None
    else:
        selected_task = None

st.divider()

# ──────────────────────────────────────────────────────────────────────────────
# TIMER DISPLAY
# ──────────────────────────────────────────────────────────────────────────────

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
    value=fmt(remaining_secs),
)

if active_task_data and not st.session_state.interval_queue:
    planned_queue = build_interval_queue(active_task_data)
    preview = " → ".join(
        f"{item['label']} ({fmt(item['seconds'])})" for item in planned_queue
    )
    st.caption(f"Planned sequence: {preview}")

btn_col1, btn_col2, btn_col3 = st.columns(3)
task_is_complete = bool(active_task_data and active_task_data["is_complete"])
current_key = _active_task_key()
can_resume = (
    bool(st.session_state.interval_queue)
    and not st.session_state.timer_running
    and st.session_state.current_task_key == current_key
)

with btn_col1:
    if st.session_state.timer_running:
        if st.button("⏸ Pause", use_container_width=True):
            _pause_timer()
            st.rerun()
    else:
        button_label = "▶ Resume Interval" if can_resume else "▶ Start Task Plan"
        start_disabled = active_task_data is None or task_is_complete
        if st.button(
            button_label,
            disabled=start_disabled,
            use_container_width=True,
            type="primary",
        ):
            if can_resume:
                _resume_queue()
            else:
                _start_new_queue_for_active_task()
            st.rerun()

with btn_col2:
    if st.button("🔄 Reset Timer", use_container_width=True):
        _reset_timer()
        st.rerun()

with btn_col3:
    if active_task_data:
        if not task_is_complete:
            if st.button("✅ Mark Task Complete", use_container_width=True):
                active_task_data["is_complete"] = True
                _reset_timer()
                st.rerun()
        else:
            if st.button("↩ Reopen Task", use_container_width=True):
                active_task_data["is_complete"] = False
                st.rerun()

st.divider()

# ──────────────────────────────────────────────────────────────────────────────
# ACTIVE TASK DETAIL PANEL
# ──────────────────────────────────────────────────────────────────────────────

if active_task_data:
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

        # Changing plan values invalidates any currently running queue.
        _reset_timer()
        if active_task_data["completed_work_chunks"] < active_task_data["total_work_chunks"]:
            active_task_data["is_complete"] = False

        st.success("Task plan updated. Start again to run the new interval sequence.")
        st.rerun()

    st.divider()

# ──────────────────────────────────────────────────────────────────────────────
# GROUP PROGRESS PANEL
# ──────────────────────────────────────────────────────────────────────────────

if st.session_state.active_group and st.session_state.active_group in st.session_state.groups:
    g_data = st.session_state.groups[st.session_state.active_group]
    tasks = g_data["tasks"]

    st.subheader(f"📊 Group Progress — {st.session_state.active_group}")

    if tasks:
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks.values() if t["is_complete"])
        group_ratio = completed_tasks / total_tasks

        prog_col, metric_col = st.columns([4, 1])
        with prog_col:
            st.progress(group_ratio, text=f"{int(group_ratio * 100)}% of tasks complete")
        with metric_col:
            st.metric("Tasks Done", f"{completed_tasks} / {total_tasks}")

        st.caption("Work-chunk progress per task:")
        for t_name, t_data in tasks.items():
            chunk_ratio = min(
                t_data["completed_work_chunks"] / t_data["total_work_chunks"],
                1.0,
            )
            icon = "✅" if t_data["is_complete"] else "🔄"
            name_col, bar_col, count_col = st.columns([2, 5, 2])
            name_col.caption(f"{icon} {t_name}")
            bar_col.progress(chunk_ratio)
            count_col.caption(
                f"{t_data['completed_work_chunks']}/{t_data['total_work_chunks']} chunks"
            )
    else:
        st.info("No tasks in this group yet. Add one in the sidebar.")


# ──────────────────────────────────────────────────────────────────────────────
# TIMER TICK  (must be at the very end of the script)
# ──────────────────────────────────────────────────────────────────────────────
#
# While timer_running is True, we sleep 1 second and rerun. That rerun updates
# the countdown metric and checks whether the current interval hit zero.

if st.session_state.timer_running:
    time.sleep(1)
    st.rerun()
