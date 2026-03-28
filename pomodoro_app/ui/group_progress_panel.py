import streamlit as st


def render_group_progress_panel() -> None:
    """Render active-group completion and per-task work-chunk progress."""
    if not st.session_state.active_group:
        return

    if st.session_state.active_group not in st.session_state.groups:
        return

    group_data = st.session_state.groups[st.session_state.active_group]
    tasks = group_data["tasks"]

    st.subheader(f"📊 Group Progress — {st.session_state.active_group}")

    if not tasks:
        st.info("No tasks in this group yet. Add one in the sidebar.")
        return

    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks.values() if task["is_complete"])
    group_ratio = completed_tasks / total_tasks

    prog_col, metric_col = st.columns([4, 1])
    with prog_col:
        st.progress(group_ratio, text=f"{int(group_ratio * 100)}% of tasks complete")
    with metric_col:
        st.metric("Tasks Done", f"{completed_tasks} / {total_tasks}")

    st.caption("Work-chunk progress per task:")
    for task_name, task_data in tasks.items():
        chunk_ratio = min(
            task_data["completed_work_chunks"] / task_data["total_work_chunks"],
            1.0,
        )
        icon = "✅" if task_data["is_complete"] else "🔄"
        name_col, bar_col, count_col = st.columns([2, 5, 2])
        name_col.caption(f"{icon} {task_name}")
        bar_col.progress(chunk_ratio)
        count_col.caption(
            f"{task_data['completed_work_chunks']}/{task_data['total_work_chunks']} chunks"
        )
