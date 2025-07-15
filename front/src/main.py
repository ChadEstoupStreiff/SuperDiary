import streamlit as st
from pages import (
    PAGE_AUDIO_RECORD,
    PAGE_CALENDAR,
    PAGE_CHAT,
    PAGE_DASHBOARD,
    PAGE_EXPLORER,
    PAGE_NOTES,
    PAGE_PROJECTS,
    PAGE_SETTINGS,
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
        PAGE_CALENDAR,
        PAGE_PROJECTS,
        PAGE_EXPLORER,
        PAGE_NOTES,
        PAGE_AUDIO_RECORD,
        PAGE_CHAT,
        PAGE_SETTINGS,
    ]
    if "file_to_see" in st.session_state:
        pages.insert(4, PAGE_VIEWER)

    pg = st.navigation(
        pages,
        expanded=True,
    )
    if "toast_for_rerun" in st.session_state:
        for message, icon in st.session_state.toast_for_rerun:
            st.toast(message, icon=icon)
        del st.session_state.toast_for_rerun
    pg.run()
