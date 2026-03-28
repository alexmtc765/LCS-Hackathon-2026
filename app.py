"""
app.py — Pomodoro Timer with Task Group Tracking
=================================================
A single-file Streamlit prototype.  All data lives in st.session_state
(no database, no file I/O) and is lost when the browser tab is closed.

Run with:
    streamlit run app.py
"""

import time
import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────────────────────────

POMODORO_SECONDS = 25 * 60   # standard 25-minute Pomodoro
# ↑  Change this to e.g. 10 for quick testing during the hackathon.

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
# Streamlit re-runs this entire script on every user interaction, so we guard
# each key with "if key not in st.session_state" to avoid wiping data on
# every rerun.
#
# Root data structure stored in st.session_state.groups:
#
#   {
#       "Math": {
#           "tasks": {
#               "Vectors 1.1": {
#                   "target_sessions":    4,
#                   "completed_sessions": 2,
#                   "is_complete":        False,
#               },
#               "Vectors 1.2": { ... },
#           }
#       },
#       "Writing": { "tasks": { ... } },
#   }
#
# ──────────────────────────────────────────────────────────────────────────────

def _init_state() -> None:
    """Set default values for every session-state key we rely on."""

    # ── Data store ────────────────────────────────────────────────────────────
    if "groups" not in st.session_state:
        st.session_state.groups: dict = {}

    # ── Currently selected group / task ───────────────────────────────────────
    if "active_group" not in st.session_state:
        st.session_state.active_group: str | None = None

    if "active_task" not in st.session_state:
        st.session_state.active_task: str | None = None

    # ── Timer state ───────────────────────────────────────────────────────────
    # timer_running        — True while the countdown is ticking.
    # timer_start_time     — time.time() snapshot of when Start/Resume was pressed.
    # timer_remaining_at_start — seconds left when the timer was (last) started
    #                            or resumed after a pause.
    # session_just_completed   — one-shot flag; set to True the instant a 25-min
    #                            session finishes so we can fire st.balloons().

    if "timer_running" not in st.session_state:
        st.session_state.timer_running: bool = False

    if "timer_start_time" not in st.session_state:
        st.session_state.timer_start_time: float | None = None

    if "timer_remaining_at_start" not in st.session_state:
        st.session_state.timer_remaining_at_start: float = POMODORO_SECONDS

    if "session_just_completed" not in st.session_state:
        st.session_state.session_just_completed: bool = False


_init_state()


# ──────────────────────────────────────────────────────────────────────────────
# TIMER HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def get_remaining_seconds() -> float:
    """
    Calculate how many seconds are left on the current timer.

    If the timer is paused (or not yet started), we simply return the last
    saved value.  If it is running, we compute:

        remaining = (seconds_saved_at_last_start) - (time_elapsed_since_start)
    """
    if not st.session_state.timer_running:
        return st.session_state.timer_remaining_at_start

    elapsed = time.time() - st.session_state.timer_start_time
    remaining = st.session_state.timer_remaining_at_start - elapsed
    return max(0.0, remaining)


def fmt(seconds: float) -> str:
    """Format a number of seconds as a MM:SS string, e.g. '24:59'."""
    s = int(seconds)
    return f"{s // 60:02d}:{s % 60:02d}"


def _start_timer() -> None:
    """Begin (or resume) the countdown from the current remaining seconds."""
    st.session_state.timer_running = True
    st.session_state.timer_start_time = time.time()
    # timer_remaining_at_start keeps whatever value was there:
    #   • full POMODORO_SECONDS on a fresh start (set by _reset_timer)
    #   • partial seconds on a resume after pause (set by _pause_timer)


def _pause_timer() -> None:
    """Freeze the countdown, saving how many seconds were left."""
    if st.session_state.timer_running:
        # Capture remaining BEFORE we flip the running flag
        st.session_state.timer_remaining_at_start = get_remaining_seconds()
        st.session_state.timer_running = False
        st.session_state.timer_start_time = None


def _reset_timer() -> None:
    """Stop the timer and restore it to the full Pomodoro duration."""
    st.session_state.timer_running = False
    st.session_state.timer_start_time = None
    st.session_state.timer_remaining_at_start = float(POMODORO_SECONDS)
    st.session_state.session_just_completed = False


def _complete_session() -> None:
    """
    Called automatically when the countdown reaches 00:00.

    1. Increments completed_sessions on the active task.
    2. Auto-marks the task complete if its target has been reached.
    3. Resets the timer so a new session can be started.
    4. Sets the one-shot flag so the UI can fire st.balloons().
    """
    g = st.session_state.active_group
    t = st.session_state.active_task

    # Guard: only act if a valid group + task is selected
    if g and t and g in st.session_state.groups:
        task = st.session_state.groups[g]["tasks"].get(t)
        if task:
            task["completed_sessions"] += 1
            # Auto-complete when the user hits their target
            if task["completed_sessions"] >= task["target_sessions"]:
                task["is_complete"] = True

    _reset_timer()
    st.session_state.session_just_completed = True  # triggers balloons below


# ──────────────────────────────────────────────────────────────────────────────
# ZERO-CROSSING CHECK  (runs before any UI is rendered)
# ──────────────────────────────────────────────────────────────────────────────
#
# Every time Streamlit reruns this script (once per second while the timer is
# active), we check whether the clock has hit zero.  Doing this check before
# the UI is rendered ensures that the completion message appears in the same
# frame that detects the end of the session.

if st.session_state.timer_running and get_remaining_seconds() <= 0:
    _complete_session()  # sets session_just_completed = True and resets timer


# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR — GROUP & TASK MANAGEMENT
# ──────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("📋 Groups & Tasks")

    # ── Create a new Group ────────────────────────────────────────────────────
    st.subheader("➕ New Group")
    new_group_name = st.text_input(
        "Group name",
        placeholder="e.g. Math, Writing, Coding…",
        key="new_group_input",
    )
    if st.button("Create Group", use_container_width=True):
        name = new_group_name.strip()
        if not name:
            st.warning("Please enter a group name.")
        elif name in st.session_state.groups:
            st.warning(f'"{name}" already exists.')
        else:
            # Each group stores a dict of tasks keyed by task name
            st.session_state.groups[name] = {"tasks": {}}
            st.success(f'Group "{name}" created!')
            st.rerun()

    st.divider()

    # ── Add a Task to an existing Group ──────────────────────────────────────
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
        target_sessions = st.number_input(
            "Target Pomodoro sessions",
            min_value=1,
            max_value=20,
            value=4,
            step=1,
            key="target_sessions_input",
        )
        if st.button("Add Task", use_container_width=True):
            task_name = new_task_name.strip()
            if not task_name:
                st.warning("Please enter a task name.")
            elif task_name in st.session_state.groups[group_for_task]["tasks"]:
                st.warning(f'"{task_name}" already exists in "{group_for_task}".')
            else:
                # Store the task as a nested dict inside the group's "tasks" dict.
                # This is the core data structure that the timer logic updates.
                st.session_state.groups[group_for_task]["tasks"][task_name] = {
                    "target_sessions": int(target_sessions),
                    "completed_sessions": 0,
                    "is_complete": False,
                }
                st.success(f'"{task_name}" added to "{group_for_task}"!')
                st.rerun()
    else:
        st.info("Create a group first.")

    st.divider()

    # ── Quick overview of all groups/tasks ────────────────────────────────────
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
                            f"{t_data['completed_sessions']}/{t_data['target_sessions']} sessions"
                        )


# ──────────────────────────────────────────────────────────────────────────────
# MAIN AREA
# ──────────────────────────────────────────────────────────────────────────────

st.title("🍅 Pomodoro Timer")

# ── Completion feedback (fires once per completed session) ───────────────────
if st.session_state.session_just_completed:
    st.balloons()
    st.success("🎉 Pomodoro complete! Great work — take a short break.")
    # Clear the flag immediately so it doesn't fire again on the next rerun
    st.session_state.session_just_completed = False

# ── Group / Task selectors ────────────────────────────────────────────────────
col_g, col_t = st.columns(2)

with col_g:
    group_options = list(st.session_state.groups.keys())
    if group_options:
        # Keep the previously active group selected if it still exists
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
        # When the user picks a different group, reset the task and timer
        if selected_group != st.session_state.active_group:
            st.session_state.active_group = selected_group
            st.session_state.active_task = None
            _reset_timer()
            st.rerun()
        else:
            st.session_state.active_group = selected_group
    else:
        st.info("👈 Create a group in the sidebar to get started.")
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
            # When the user picks a different task, reset the timer
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

# Resolve a direct reference to the active task's data dict (or None)
active_task_data: dict | None = None
if (
    st.session_state.active_group
    and st.session_state.active_task
    and st.session_state.active_group in st.session_state.groups
):
    active_task_data = (
        st.session_state.groups[st.session_state.active_group]["tasks"]
        .get(st.session_state.active_task)
    )

# st.empty() gives us a placeholder we can overwrite in-place on every rerun.
# The timer tick at the bottom of the file calls st.rerun() every second,
# which re-executes this whole script and updates the metric below.
timer_placeholder = st.empty()

remaining_secs = get_remaining_seconds()
timer_placeholder.metric(
    label="⏱ Time Remaining",
    value=fmt(remaining_secs),
)

# ── Control buttons ───────────────────────────────────────────────────────────
btn_col1, btn_col2, btn_col3 = st.columns(3)

task_is_complete = bool(active_task_data and active_task_data["is_complete"])

with btn_col1:
    if not st.session_state.timer_running:
        # Disable Start if no task is selected or the task is already marked done
        start_disabled = active_task_data is None or task_is_complete
        if st.button(
            "▶ Start Pomodoro",
            disabled=start_disabled,
            use_container_width=True,
            type="primary",
        ):
            _start_timer()
            st.rerun()
    else:
        if st.button("⏸ Pause", use_container_width=True):
            _pause_timer()
            st.rerun()

with btn_col2:
    if st.button("🔄 Reset Timer", use_container_width=True):
        _reset_timer()
        st.rerun()

with btn_col3:
    # Toggle between "Mark Complete" and "Reopen Task"
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

    m1, m2, m3 = st.columns(3)
    m1.metric("Sessions Completed", active_task_data["completed_sessions"])
    m2.metric("Target Sessions", active_task_data["target_sessions"])
    m3.metric("Status", "✅ Done" if active_task_data["is_complete"] else "🔄 In Progress")

    # Allow extending the target if the user needs more sessions than planned.
    # The min_value is clamped to completed+1 so the target always stays
    # ahead of what has already been done.
    st.caption("Need more time? Adjust the session target:")
    new_target = st.number_input(
        "New target sessions",
        min_value=active_task_data["completed_sessions"] + 1,
        max_value=50,
        value=active_task_data["target_sessions"],
        step=1,
        key="extend_target_input",
    )
    if st.button("Update Target"):
        active_task_data["target_sessions"] = int(new_target)
        # If the user raised the target, the task is no longer auto-complete
        if active_task_data["completed_sessions"] < active_task_data["target_sessions"]:
            active_task_data["is_complete"] = False
        st.success("Target updated!")
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
        group_ratio = completed_tasks / total_tasks  # value in [0.0, 1.0]

        # Top-line progress bar (tasks complete / total tasks)
        prog_col, metric_col = st.columns([4, 1])
        with prog_col:
            st.progress(group_ratio, text=f"{int(group_ratio * 100)}% of tasks complete")
        with metric_col:
            st.metric("Tasks Done", f"{completed_tasks} / {total_tasks}")

        # Per-task session progress bars
        st.caption("Session progress per task:")
        for t_name, t_data in tasks.items():
            # Clamp to 1.0 in case completed_sessions ever exceeds target
            session_ratio = min(
                t_data["completed_sessions"] / t_data["target_sessions"], 1.0
            )
            icon = "✅" if t_data["is_complete"] else "🔄"
            name_col, bar_col, count_col = st.columns([2, 5, 1])
            name_col.caption(f"{icon} {t_name}")
            bar_col.progress(session_ratio)
            count_col.caption(f"{t_data['completed_sessions']}/{t_data['target_sessions']}")
    else:
        st.info("No tasks in this group yet — add one in the sidebar.")


# ──────────────────────────────────────────────────────────────────────────────
# TIMER TICK  (must be at the very end of the script)
# ──────────────────────────────────────────────────────────────────────────────
#
# How live countdown works in Streamlit:
#
#   1. The user presses "Start Pomodoro".
#   2. _start_timer() saves time.time() into session state and flips
#      timer_running = True.
#   3. We hit this block — time.sleep(1) pauses execution for one second.
#   4. st.rerun() tells Streamlit to re-execute this entire script from the
#      top, which recomputes get_remaining_seconds() and overwrites the
#      timer metric with the updated value.
#   5. This loop repeats until either:
#        a. The user presses Pause or Reset  (timer_running becomes False), or
#        b. get_remaining_seconds() reaches 0, triggering _complete_session().
#
# The 1-second sleep only occurs when the timer is actively ticking, so it
# does NOT block user interactions when the timer is stopped.

if st.session_state.timer_running:
    time.sleep(1)
    st.rerun()
