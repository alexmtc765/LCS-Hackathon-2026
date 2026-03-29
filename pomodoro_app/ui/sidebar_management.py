import streamlit as st

from pomodoro_app.state.session_state import get_groups, persist_data
from pomodoro_app.timer.controller import (
    clear_runtime_snapshot_for_task,
    persist_last_selected_task_context,
    reset_timer,
)


def render_task_management_tab() -> None:
    """Render task and group creation UI in the Task Management tab."""
    groups = get_groups()

    st.subheader("Groups")
    col_new_group, _ = st.columns([3, 2])
    with col_new_group:
        new_group_name = st.text_input(
            "Create Group",
            placeholder="e.g. Math, Writing, Coding",
            key="new_group_input",
        )
        if st.button("Create Group", use_container_width=True):
            name = new_group_name.strip()
            if not name:
                st.warning("Please enter a group name.")
            elif name in groups:
                st.warning(f'"{name}" already exists.')
            else:
                groups[name] = {"tasks": {}}
                persist_data()
                st.success(f'Group "{name}" created!')
                st.rerun()

    if groups:
        with st.expander("Delete Group", expanded=False):
            group_to_delete = st.selectbox(
                "Select group to delete",
                options=list(groups.keys()),
                key="delete_group_select",
            )
            task_count = len(groups[group_to_delete]["tasks"])
            st.warning(
                f'This will permanently delete group "{group_to_delete}" '
                f"and all {task_count} tasks in it."
            )

            confirm_group_delete = st.checkbox(
                "I understand this will delete the entire group and all tasks.",
                key="confirm_group_delete_checkbox",
            )
            if st.button(
                "Delete Group and All Tasks",
                type="secondary",
                use_container_width=True,
                key="delete_group_button",
            ):
                if not confirm_group_delete:
                    st.warning("Please confirm group deletion before continuing.")
                else:
                    task_names = set(groups[group_to_delete]["tasks"].keys())

                    # Remove per-task totals for this group.
                    group_prefix = f"{group_to_delete} :: "
                    totals_keys = [
                        key
                        for key in st.session_state.data["task_totals"].keys()
                        if key.startswith(group_prefix)
                    ]
                    for key in totals_keys:
                        st.session_state.data["task_totals"].pop(key, None)

                    # Remove history rows tied to tasks in this group.
                    st.session_state.data["session_logs"] = [
                        row
                        for row in st.session_state.data["session_logs"]
                        if row.get("task_name") not in task_names
                    ]

                    # Remove runtime snapshots for tasks in this group.
                    for task_name in task_names:
                        clear_runtime_snapshot_for_task((group_to_delete, task_name))

                    del groups[group_to_delete]

                    if st.session_state.active_group == group_to_delete:
                        st.session_state.active_group = None
                        st.session_state.active_task = None
                        reset_timer()
                        persist_last_selected_task_context()

                    persist_data()
                    st.success(f'Deleted group "{group_to_delete}" and all tasks in it.')
                    st.rerun()

    st.divider()
    st.subheader("Tasks")

    if groups:
        group_for_task = st.selectbox(
            "Add task to group",
            options=list(groups.keys()),
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
            st.caption("Break minutes are ignored when Number of Breaks is 0.")

        if st.button("Add Task", use_container_width=True):
            task_name = new_task_name.strip()
            if not task_name:
                st.warning("Please enter a task name.")
            elif task_name in groups[group_for_task]["tasks"]:
                st.warning(f'"{task_name}" already exists in "{group_for_task}".')
            else:
                total_work_chunks = int(number_of_breaks_input) + 1
                groups[group_for_task]["tasks"][task_name] = {
                    "total_work_minutes": int(total_work_minutes_input),
                    "number_of_breaks": int(number_of_breaks_input),
                    "total_break_minutes": int(total_break_minutes_input),
                    "total_work_chunks": total_work_chunks,
                    "completed_work_chunks": 0,
                    "total_time_minutes_spent": 0.0,
                    "is_complete": False,
                }
                persist_data()
                st.success(f'"{task_name}" added to "{group_for_task}"!')
                st.rerun()
    else:
        st.info("Create a group first.")

    st.divider()
    st.subheader("Overview")

    if not groups:
        st.caption("No groups yet.")
        return

    for group_name, group_data in groups.items():
        with st.expander(f"📁 {group_name}"):
            if not group_data["tasks"]:
                st.caption("No tasks yet.")
            else:
                for task_name, task_data in list(group_data["tasks"].items()):
                    info_col, delete_col = st.columns([5, 1])
                    icon = "✅" if task_data["is_complete"] else "🔄"
                    with info_col:
                        st.caption(
                            f"{icon} **{task_name}** — "
                            f"{task_data['completed_work_chunks']}/{task_data['total_work_chunks']} work chunks"
                        )
                        st.caption(
                            f"{task_data['total_work_minutes']}m work | "
                            f"{task_data['number_of_breaks']} breaks | "
                            f"{task_data['total_break_minutes']}m total break | "
                            f"{task_data.get('total_time_minutes_spent', 0.0)}m spent"
                        )
                    with delete_col:
                        if st.button(
                            "Delete",
                            key=f"delete_task_overview_{group_name}_{task_name}",
                            type="secondary",
                            use_container_width=True,
                        ):
                            del groups[group_name]["tasks"][task_name]
                            clear_runtime_snapshot_for_task((group_name, task_name))

                            totals_key = f"{group_name} :: {task_name}"
                            st.session_state.data["task_totals"].pop(totals_key, None)

                            if (
                                st.session_state.active_group == group_name
                                and st.session_state.active_task == task_name
                            ):
                                st.session_state.active_task = None
                                reset_timer()
                                persist_last_selected_task_context()

                            persist_data()
                            st.success(f'Deleted task "{task_name}" from "{group_name}".')
                            st.rerun()
