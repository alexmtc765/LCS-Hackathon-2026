import json
import os
from copy import deepcopy
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = PROJECT_ROOT / "data.json"

DEFAULT_DATA = {
    "groups": {},
    "task_totals": {},
    "session_logs": [],
    "settings": {
        "sound_type": "Relaxing",
        "target_work_hours": 4.0,
    },
    "runtime_state": {
        "task_runs": {},
        "last_selected_group": None,
        "last_selected_task": None,
    },
}


def get_default_data() -> dict:
    """Return a fresh copy of the default persisted data structure."""
    return deepcopy(DEFAULT_DATA)


def _normalize_data(data: dict) -> dict:
    """Ensure required top-level keys exist with safe default shapes."""
    normalized = deepcopy(DEFAULT_DATA)

    if isinstance(data, dict):
        if isinstance(data.get("groups"), dict):
            normalized["groups"] = data["groups"]
        if isinstance(data.get("task_totals"), dict):
            normalized["task_totals"] = data["task_totals"]
        if isinstance(data.get("session_logs"), list):
            normalized["session_logs"] = data["session_logs"]
        if isinstance(data.get("settings"), dict):
            normalized["settings"].update(data["settings"])
        if isinstance(data.get("runtime_state"), dict):
            runtime_state = data["runtime_state"]
            if isinstance(runtime_state.get("task_runs"), dict):
                normalized["runtime_state"]["task_runs"] = runtime_state["task_runs"]
            normalized["runtime_state"]["last_selected_group"] = runtime_state.get(
                "last_selected_group"
            )
            normalized["runtime_state"]["last_selected_task"] = runtime_state.get(
                "last_selected_task"
            )

    if normalized["settings"].get("sound_type") not in ("Harsh", "Relaxing"):
        normalized["settings"]["sound_type"] = "Relaxing"

    try:
        normalized["settings"]["target_work_hours"] = float(
            normalized["settings"].get("target_work_hours", 4.0)
        )
    except (TypeError, ValueError):
        normalized["settings"]["target_work_hours"] = 4.0

    return normalized


def load_data() -> dict:
    """
    Load persisted data from data.json.

    Behavior:
    - If file is missing, creates it with defaults.
    - If JSON is corrupted, creates a timestamped backup and resets to defaults.
    - Always returns normalized data shape.
    """
    if not DATA_FILE.exists():
        fresh_defaults = get_default_data()
        save_data(fresh_defaults)
        return fresh_defaults

    try:
        with DATA_FILE.open("r", encoding="utf-8") as infile:
            raw = json.load(infile)
        data = _normalize_data(raw)
    except (json.JSONDecodeError, OSError):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = DATA_FILE.with_name(f"data.corrupt.{timestamp}.json")

        if os.path.exists(str(DATA_FILE)):
            try:
                DATA_FILE.replace(backup_path)
            except OSError:
                pass

        data = get_default_data()
        save_data(data)

    return data


def save_data(data: dict) -> None:
    """Persist data atomically to reduce risk of partial writes."""
    normalized = _normalize_data(data)
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    temp_file = DATA_FILE.with_suffix(".tmp")
    with temp_file.open("w", encoding="utf-8") as outfile:
        json.dump(normalized, outfile, indent=2)

    temp_file.replace(DATA_FILE)
