import streamlit as st

from views.dashboard import dashboard
from views.explorer import explorer
from views.audio_record import audio_record
from views.settings import settings

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
            ),
            st.Page(
                explorer,
                title="Explorer",
                icon="🔍",
            ),
            st.Page(
                audio_record,
                title="Audio Record",
                icon="🎤",
            ),
            st.Page(
                settings,
                title="Settings",
                icon="⚙️",
            ),
        ]
    )
    pg.run()
