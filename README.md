<div align="center">

# 🪤 FinIt

**A modular Pomodoro productivity timer — built for the [LCS Hack the Future 2026](https://github.com/Apollo8132) hackathon.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![JSON](https://img.shields.io/badge/Storage-JSON-F5A623?style=for-the-badge&logo=json&logoColor=white)](https://www.json.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)
[![Hackathon](https://img.shields.io/badge/LCS-Hack%20the%20Future%202026-7C3AED?style=for-the-badge)](https://github.com/Apollo8132)

---

*Stay focused. Use FinIt 🪤*

</div>

---

## 📖 Overview

**FinIt** is a feature packed productivity app to help you stay focused.

FinIt lets you organise your work into **groups** and **tasks**, custom-configure work/break intervals per task, and watch your progress in real time. Every session is persisted locally so nothing is lost on a page refresh — even mid-timer.

---
## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- `pip`

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Apollo8132/LCS-Hackathon-2026.git
cd LCS-Hackathon-2026

# 2. (Recommended) Create a virtual environment
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate        # Windows

# 3. Install dependencies
pip install streamlit

# 4. Run the app
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## ✨ Features

| Category | What it does |
|---|---|
| **⏱ Pomodoro Timer** | Live `MM:SS` countdown with start, pause, reset, skip, and complete controls |
| **🗂 Groups & Tasks** | Organise tasks into named groups; configure work time, break count, and break duration per task |
| **🔁 Smart Intervals** | Automatically interleaves work and break chunks; auto-advances on countdown completion |
| **📊 Productivity Dashboard** | Daily target tracking, work-time bar chart, and full session history table |
| **💾 Persistent State** | Timer snapshots survive page refreshes via atomic JSON writes |
| **🔊 Sound Alerts** | Plays `.mp3` alerts on interval transitions — choose between "Harsh" or "Relaxing" sound packs |
| **🎨 Glassmorphism UI** | Custom CSS theme with responsive light & dark mode support |
| **🧹 Data Management** | Full data reset with a confirmation safeguard built into Settings |

---

## 🖼 Screenshots

<table>
  <tr>
    <td align="center"><strong>Task Timer</strong></td>
    <td align="center"><strong>Group Overviews</strong></td>
  </tr>
  <tr>
    <td><img src="images/Task Timer.png" alt="Task Timer" width="100%"/></td>
    <td><img src="images/Group Overviews.png" alt="Group Overviews" width="100%"/></td>
  </tr>
  <tr>
    <td align="center"><strong>Productivity Dashboard</strong></td>
    <td align="center"><strong>Session History</strong></td>
  </tr>
  <tr>
    <td><img src="images/Productivity Dashboard.png" alt="Productivity Dashboard" width="100%"/></td>
    <td><img src="images/Session History.png" alt="Session History" width="100%"/></td>
  </tr>
</table>

---

### Adding Custom Sounds *(optional)*

Drop `.mp3` files into the appropriate folder to enable audio alerts:

```
sounds/
├── harsh/       ← "Harsh" sound pack (e.g. alarm tones)
└── relaxing/    ← "Relaxing" sound pack (e.g. gentle sounds)
```

Files are matched by event name prefix (`work_end`, `break_end`, `task_end`) or chosen randomly if no prefix match is found.

---

## 🗺 How It Works

### Timer Flow

```
Start Task
    │
    ▼
[Work Chunk 1] ──► [Break 1] ──► [Work Chunk 2] ──► ... ──► [Work Chunk N]
                                                                     │
                                                             Task Complete 🎉
```

Each task defines:
- **Total work minutes** — split evenly across work chunks
- **Number of breaks** — determines how many work ↔ break transitions occur
- **Total break minutes** — split evenly across breaks

### Data Persistence

All data is stored locally in `data.json`.

### Persistance

Tasks and groups are saved and are persistant between reloading.

---

## 🏗 Project Structure

```
LCS-Hackathon-2026/
├── app.py                          # Entry point
├── data.json                       # Persisted app data
├── images/                         # Screenshots
├── sounds/
│   ├── harsh/                      # Harsh sound pack (.mp3)
│   └── relaxing/                   # Relaxing sound pack (.mp3)
└── pomodoro_app/
    ├── media/
    │   └── audio_player.py         # Base64 audio injection
    ├── state/
    │   └── session_state.py        # st.session_state initialisation
    ├── storage/
    │   └── json_store.py           # Atomic JSON read/write
    ├── timer/
    │   ├── controller.py           # Tick logic & interval advancement
    │   └── intervals.py            # Interval queue builder
    └── ui/
        ├── layout.py               # Top-level tab renderer
        ├── dashboard_tab.py        # Metrics, charts, history
        ├── group_progress_panel.py # Per-group progress bars
        ├── notifications.py        # Alerts, balloons, sounds
        ├── selectors.py            # Group/task dropdowns
        ├── settings_panel.py       # Settings tab & danger zone
        ├── sidebar_management.py   # Group/task CRUD sidebar
        ├── task_details_panel.py   # Active task metrics & editor
        ├── theme.py                # UI Theme
        └── timer_panel.py          # Timer display & controls
```

---

## 🛠 Tech Stack

| Tool | Role |
|---|---|
| **[Python](https://www.python.org/)** | Core language |
| **[Streamlit](https://streamlit.io/)** | Web UI framework |
| **JSON** | Lightweight local data storage |
| **Python stdlib** (`pathlib`, `time`, `datetime`, `base64`, `random`) | Supporting utilities |

---

## 👤 Author's

**Apollo8132** — built for the **LCS Hack the Future 2026** hackathon.
- Alexandru Motoc
- Omar Naveed
- Dotayen Degen
- Christian Lara
---

<div align="center">
  <em>Made with ☕ and 🥲</em>
</div>
