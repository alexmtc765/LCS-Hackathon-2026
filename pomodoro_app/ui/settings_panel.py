import streamlit as st

from pomodoro_app.state.session_state import persist_data
from pomodoro_app.storage.json_store import get_default_data


def render_settings_sidebar() -> None:
    """Render settings controls in a sidebar expander."""
    with st.sidebar:
        with st.expander("Settings", expanded=True):
            sound_type = st.selectbox(
                "Sound Type",
                options=["Harsh", "Relaxing"],
                index=0
                if st.session_state.data["settings"].get("sound_type") == "Harsh"
                else 1,
                key="sound_type_select",
            )

            target_hours = st.number_input(
                "Target Work Hours (Daily)",
                min_value=0.5,
                max_value=24.0,
                value=float(st.session_state.data["settings"].get("target_work_hours", 4.0)),
                step=0.5,
                key="daily_target_hours_input",
            )

            changed = (
                st.session_state.data["settings"].get("sound_type") != sound_type
                or float(st.session_state.data["settings"].get("target_work_hours", 4.0))
                != float(target_hours)
            )
            if changed:
                st.session_state.data["settings"]["sound_type"] = sound_type
                st.session_state.data["settings"]["target_work_hours"] = float(target_hours)
                persist_data()
                st.caption("Settings saved.")


def render_settings_tab() -> None:
    """Render duplicated settings panel in dedicated Settings tab."""
    st.subheader("App Settings")
    st.caption("These values persist to data.json and are shared across tabs.")

    sound_type = st.selectbox(
        "Sound Type",
        options=["Harsh", "Relaxing"],
        index=0 if st.session_state.data["settings"].get("sound_type") == "Harsh" else 1,
        key="settings_tab_sound_type",
    )
    target_hours = st.number_input(
        "Target Work Hours for Today",
        min_value=0.5,
        max_value=24.0,
        value=float(st.session_state.data["settings"].get("target_work_hours", 4.0)),
        step=0.5,
        key="settings_tab_target_hours",
    )

    if st.button("Save Settings", key="save_settings_button"):
        st.session_state.data["settings"]["sound_type"] = sound_type
        st.session_state.data["settings"]["target_work_hours"] = float(target_hours)
        persist_data()
        st.success("Settings saved to data.json")

    st.divider()
    st.subheader("Danger Zone")
    st.warning("Delete all app data, including all groups, tasks, and history.")

    confirm_delete_all = st.checkbox(
        "I understand this will permanently delete all saved data.",
        key="confirm_delete_all_checkbox",
    )
    delete_phrase = st.text_input(
        "Type DELETE to confirm",
        key="delete_all_phrase_input",
    )

    if st.button(
        "Delete All Data",
        type="secondary",
        use_container_width=True,
        key="delete_all_data_button",
    ):
        if not confirm_delete_all or delete_phrase.strip() != "DELETE":
            st.error("Confirmation failed. Check the box and type DELETE exactly.")
        else:
            st.session_state.data = get_default_data()
            st.session_state.active_group = None
            st.session_state.active_task = None
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
            st.session_state.pending_sound_event = ""

            persist_data()
            st.success("All data deleted.")
            st.rerun()
