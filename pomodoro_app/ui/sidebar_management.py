import streamlit as st


def render_sidebar_group_and_task_management() -> None:
    """Render sidebar controls for creating groups and task plans."""
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
            for group_name, group_data in st.session_state.groups.items():
                with st.expander(f"📁 {group_name}"):
                    if not group_data["tasks"]:
                        st.caption("No tasks yet.")
                    else:
                        for task_name, task_data in group_data["tasks"].items():
                            icon = "✅" if task_data["is_complete"] else "🔄"
                            st.caption(
                                f"{icon} **{task_name}** — "
                                f"{task_data['completed_work_chunks']}/{task_data['total_work_chunks']} work chunks"
                            )
                            st.caption(
                                f"{task_data['total_work_minutes']}m work | "
                                f"{task_data['number_of_breaks']} breaks | "
                                f"{task_data['total_break_minutes']}m total break"
                            )
