import streamlit as st


def inject_glass_theme() -> None:
    """Inject a light/dark friendly glassmorphism style layer."""
    st.markdown(
        """
        <style>
        :root {
          --glass-bg: rgba(255, 255, 255, 0.50);
          --glass-border: rgba(255, 255, 255, 0.35);
          --glass-shadow: 0 8px 24px rgba(9, 24, 39, 0.16);
          --app-grad-a: #d7eefc;
          --app-grad-b: #f5e9d8;
          --accent: #2f8f8f;
          --text-main: #1b2733;
        }

        @media (prefers-color-scheme: dark) {
          :root {
            --glass-bg: rgba(22, 27, 37, 0.55);
            --glass-border: rgba(255, 255, 255, 0.14);
            --glass-shadow: 0 10px 30px rgba(0, 0, 0, 0.42);
            --app-grad-a: #0f1622;
            --app-grad-b: #1f1a2b;
            --accent: #5eb7b7;
            --text-main: #edf2f7;
          }
        }

        .stApp {
          background:
            radial-gradient(1200px 480px at 20% -10%, var(--app-grad-a), transparent),
            radial-gradient(1200px 480px at 80% 0%, var(--app-grad-b), transparent),
            linear-gradient(180deg, transparent, rgba(0, 0, 0, 0.05));
          color: var(--text-main);
        }

        [data-testid="stSidebar"] > div:first-child {
          background: var(--glass-bg);
          border-right: 1px solid var(--glass-border);
          backdrop-filter: blur(18px);
        }

        div[data-testid="stMetric"],
        div.stAlert,
        div[data-testid="stVerticalBlock"] > div:has(> div.stTabs),
        div[data-testid="stExpander"] {
          background: var(--glass-bg);
          border: 1px solid var(--glass-border);
          border-radius: 16px;
          box-shadow: var(--glass-shadow);
          backdrop-filter: blur(12px);
          padding: 0.35rem 0.55rem;
        }

        .stTabs [data-baseweb="tab-list"] button {
          border-radius: 10px;
        }

        .stTabs [aria-selected="true"] {
          background: color-mix(in srgb, var(--accent) 26%, transparent);
          border: 1px solid color-mix(in srgb, var(--accent) 42%, white 20%);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
