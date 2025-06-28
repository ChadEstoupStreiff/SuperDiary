import streamlit as st
from pages import (
    PAGE_AUDIO_RECORD,
    PAGE_DASHBOARD,
    PAGE_EXPLORER,
    PAGE_NOTES,
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
    # custom_style()

    pages = [
            PAGE_DASHBOARD,
            PAGE_EXPLORER,
            PAGE_NOTES,
            PAGE_AUDIO_RECORD,
            PAGE_TASKS,
            PAGE_SETTINGS,
        ]
    if "file_to_see" in st.session_state:
        pages.insert(2, PAGE_VIEWER)

    pg = st.navigation(
        pages,
        expanded=True,
    )
    pg.run()
