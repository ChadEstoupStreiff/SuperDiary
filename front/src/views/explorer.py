import os

import requests
import streamlit as st
from utils import download_and_display_file
import time


def open_file(file):
    if file is None:
        del st.session_state.file_to_see
    else:
        st.session_state.file_to_see = file


def box_file(file):
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
            st.button(
                "👁️",
                on_click=open_file,
                args=(file,),
                help="Click to view file details.",
                use_container_width=True,
                key=f"view_{file}",
            )
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

@st.dialog("Delete file")
def dialog_delete_file(file):
    """
    This dialog is used to confirm the deletion of a file.
    It provides a button to delete the file and a button to cancel the action.
    """
    st.markdown(f"Are you sure you want to delete the file:\n  **{os.path.basename(file)}**?\n   This action cannot be undone.")
    if st.button("Delete 🗑️", use_container_width=True):
        resulst = requests.delete(f"http://back:80/files/delete/{file}")
        if resulst.status_code == 200:
            st.success("File deleted successfully.")
            del st.session_state.file_to_see
            st.rerun()
        else:
            st.error("Failed to delete the file. Please try again.")

def see_file(file):
    st.divider()
    date = file.split("/")[2]
    subfolder = file.split("/")[3]
    file_name = os.path.basename(file)
    st.markdown(f"#### {file_name}")
    st.caption(f"**Date:** {date}")
    st.caption(f"**Subfolder:** {subfolder}")
    st.caption(f"**Path:** {file}")

    st.download_button(
        "📥",
        f"http://back:80/files/download/{file}",
        file_name=file_name,
        help="Click to download the file.",
        use_container_width=True,
        key=f"see_download_{file}",
    )
    if st.button(
        "🗑️",
        use_container_width=True,
        help="Click to delete the file.",
        key=f"see_delete_{file}",
    ):
        dialog_delete_file(file)

def explorer():
    """
    This function serves as a placeholder for the explorer view.
    It currently does not perform any operations or return any data.
    """
    if "file_to_see" in st.session_state:
        cols = st.columns([1, 2])
        with cols[0]:
            st.button(
                "⬅️",
                on_click=open_file,
                args=(None,),
                key="close_file",
                use_container_width=True,
                help="Click to close file details.",
            )
            see_file(st.session_state.file_to_see)

        with cols[1]:
            with st.container(border=True):
                download_and_display_file(st.session_state.file_to_see)

    else:
        st.text_input(
            "Search files",
            placeholder="Enter file name, content or keyword...",
            key="search_files",
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
        if files:
            st.write("Files in the system:")

            file_preview_infos = []
            cols = st.columns(nbr_of_files_per_line)
            for i, file in enumerate(files):
                with cols[i % nbr_of_files_per_line]:
                    file_preview_infos.append(box_file(file))

            for i, file_preview_info in enumerate(file_preview_infos):
                file_preview_container = file_preview_info
                with file_preview_container:
                    download_and_display_file(files[i])
        else:
            st.write("No files found in the system.")
