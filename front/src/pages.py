import streamlit as st

PAGE_DASHBOARD = st.Page(
    "views/dashboard.py",
    title="Dashboard",
    icon="🏠",
    url_path="dashboard",
    default=True,
)
PAGE_EXPLORER = st.Page(
    "views/explorer.py",
    title="Explorer",
    icon="🔍",
    url_path="explorer",
)
PAGE_VIEWER = st.Page(
    "views/view.py",
    title="View",
    icon="👁️",
    url_path="view",
)
PAGE_AUDIO_RECORD = st.Page(
    "views/audio_record.py",
    title="Audio Record",
    icon="🎤",
    url_path="audio_record",
)
PAGE_TASKS = st.Page(
    "views/tasks.py",
    title="Tasks",
    icon="📝",
    url_path="tasks",
)
PAGE_SETTINGS = st.Page(
    "views/settings.py",
    title="Settings",
    icon="⚙️",
    url_path="settings",
)
