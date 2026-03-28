"""
Entry point for the modular Streamlit prototype.

Run:
    streamlit run app.py
"""

import streamlit as st

from pomodoro_app.state.session_state import init_state
from pomodoro_app.timer.controller import process_timer_zero_crossing, run_timer_tick
from pomodoro_app.ui.layout import render_app_layout


st.set_page_config(
    page_title="FinIt 🪤",
    page_icon="🪤",
    layout="wide",
)


# Initialize app state before reading or writing any session keys.
init_state()

# If countdown hits zero on a rerun, advance interval flow immediately.
process_timer_zero_crossing()

# Render full UI from independent section modules.
render_app_layout()

# Keep timer live while running.
run_timer_tick()
