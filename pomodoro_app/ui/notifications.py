import streamlit as st

from pomodoro_app.media.audio_player import play_audio_event_if_needed


def render_main_notifications() -> None:
    """Render transition and completion feedback at top of main area."""
    st.title("FinIt 🪤")
    play_audio_event_if_needed()

    if st.session_state.interval_transition_message:
        st.info(st.session_state.interval_transition_message)
        st.session_state.interval_transition_message = ""

    if st.session_state.session_just_completed:
        st.balloons()
        st.success("🎉 Final work chunk complete. Task marked complete.")
        st.session_state.session_just_completed = False
