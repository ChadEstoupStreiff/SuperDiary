import streamlit as st
from pages import (
    PAGE_AUDIO_RECORD,
    PAGE_DASHBOARD,
    PAGE_EXPLORER,
    PAGE_SETTINGS,
    PAGE_TASKS,
    PAGE_VIEWER,
)

if __name__ == "__main__":
    st.set_page_config(
        page_title="Super Diary",
        page_icon="/assets/logo.png",
        layout="wide",
    )

    pg = st.navigation(
        [
            PAGE_DASHBOARD,
            PAGE_EXPLORER,
            PAGE_VIEWER,
            PAGE_AUDIO_RECORD,
            PAGE_TASKS,
            PAGE_SETTINGS,
        ]
    )
    pg.run()
