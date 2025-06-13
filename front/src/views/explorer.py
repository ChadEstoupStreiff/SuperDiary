import os

import requests
import streamlit as st
from pages import PAGE_VIEWER
from utils import download_and_display_file


def box_file(file):
    # MARK: BOX FILE
    with st.container(border=True, height=600):
        preview = st.container(
            border=True,
            height=300,
        )
        file_name = os.path.basename(file)
        date = file.split("/")[2]
        subfolder = file.split("/")[3]

        cols = st.columns(2)
        st.markdown(f"#### {file_name}")
        st.caption(f"**Date:** {date}")
        st.caption(f"**Subfolder:** {subfolder}")
        st.caption(f"**Path:** {file}")

        with cols[0]:
            if st.button(
                "👁️",
                help="Click to view file details.",
                use_container_width=True,
                key=f"view_{file}",
            ):
                st.session_state.file_to_see = file
                st.switch_page(PAGE_VIEWER)
        with cols[1]:
            st.download_button(
                "📥",
                f"http://back:80/files/download/{file}",
                file_name=file_name,
                help="Click to download the file.",
                use_container_width=True,
                key=f"download_{file}",
            )
    return preview


def explorer():
    """
    This function serves as a placeholder for the explorer view.
    It currently does not perform any operations or return any data.
    """
    # MARK: FILES LIST
    cols = st.columns([4, 1])
    with cols[0]:
        # TODO file search
        st.text_input(
            "Search files",
            placeholder="Enter file name, content or keyword...",
            key="search_files",
        )
    with cols[1]:
        # TODO fo reprenstation
        st.segmented_control(
            "Representation",
            options=[0, 1],
            format_func=lambda x: ["List", "Boxes"][x],
            default=1,
            key="representation",
        )
    st.divider()

    nbr_of_files_per_line = st.sidebar.slider(
        "Number of files per line",
        min_value=3,
        max_value=10,
        value=5,
        help="Adjust the number of files displayed per line.",
    )

    files = requests.get("http://back:80/files/list").json()
    if files and len(files) > 0:
        file_preview_infos = []
        cols = st.columns(nbr_of_files_per_line)
        for i, file in enumerate(files):
            with cols[i % nbr_of_files_per_line]:
                file_preview_infos.append(box_file(file))

        for i, file_preview_info in enumerate(file_preview_infos):
            file_preview_container = file_preview_info
            with file_preview_container:
                download_and_display_file(files[i], default_height_if_needed=250)
    else:
        st.write("No files found in the system.")


if __name__ == "__main__":
    explorer()
