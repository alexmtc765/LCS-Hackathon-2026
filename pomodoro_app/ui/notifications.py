import streamlit as st


def render_main_notifications() -> None:
    """Render transition and completion feedback at top of main area."""
    st.title("FinIt 🪤")

    if st.session_state.interval_transition_message:
        st.info(st.session_state.interval_transition_message)
        st.session_state.interval_transition_message = ""

    if st.session_state.session_just_completed:
        st.balloons()
        st.success("🎉 Final work chunk complete. Task marked complete.")
        st.session_state.session_just_completed = False
