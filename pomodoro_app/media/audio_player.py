import base64
import os
import random
from pathlib import Path

import streamlit as st


SOUNDS_ROOT = Path(__file__).resolve().parents[2] / "sounds"


def _pick_sound_file(sound_type: str, event_name: str) -> Path | None:
    """Choose a matching mp3 for an event, with graceful fallback behavior."""
    tone = sound_type.strip().lower()
    if tone not in ("harsh", "relaxing"):
        tone = "relaxing"

    folder = SOUNDS_ROOT / tone
    if not folder.exists():
        return None

    preferred = sorted(folder.glob(f"{event_name}*.mp3"))
    candidates = preferred if preferred else sorted(folder.glob("*.mp3"))
    if not candidates:
        return None

    chosen = random.choice(candidates)
    if not os.path.exists(str(chosen)):
        return None

    return chosen


def play_audio_event_if_needed() -> None:
    """Render autoplay audio tag when timer sets a pending sound event."""
    event_name = st.session_state.get("pending_sound_event", "")
    if not event_name:
        return

    # Consume the event and any tone override so we can play harsh/relaxing independently
    # of the global user setting.
    tone_override = st.session_state.get("pending_sound_tone", "")
    st.session_state.pending_sound_event = ""
    st.session_state.pending_sound_tone = ""

    settings = st.session_state.data.get("settings", {})
    sound_type = tone_override if tone_override else settings.get("sound_type", "Relaxing")

    audio_path = _pick_sound_file(sound_type, event_name)
    if audio_path is None:
        return

    try:
        audio_bytes = audio_path.read_bytes()
    except OSError:
        return

    encoded = base64.b64encode(audio_bytes).decode("ascii")
    html = (
        "<audio autoplay>"
        f"<source src=\"data:audio/mp3;base64,{encoded}\" type=\"audio/mp3\">"
        "</audio>"
    )
    st.markdown(html, unsafe_allow_html=True)
