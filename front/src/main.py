import streamlit as st

from views.dashboard import dashboard
from views.explorer import explorer
from views.audio_record import audio_record
from views.settings import settings
from views.tasks import tasks

if __name__ == "__main__":
    st.set_page_config(
        page_title="Super Diary",
        page_icon=":rocket:",
        layout="wide",
    )

    pg = st.navigation(
        [
            st.Page(
                dashboard,
                title="Dashboard",
                icon="🏠",
                url_path="dashboard",
                default=True,
            ),
            st.Page(
                explorer,
                title="Explorer",
                icon="🔍",
                url_path="explorer",
            ),
            st.Page(
                audio_record,
                title="Audio Record",
                icon="🎤",
                url_path="audio_record",
            ),
            st.Page(
                tasks,
                title="Tasks",
                icon="📝",
                url_path="tasks",
            ),
            st.Page(
                settings,
                title="Settings",
                icon="⚙️",
                url_path="settings",
            ),
        ]
    )
    pg.run()
