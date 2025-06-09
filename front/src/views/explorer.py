import os

import requests
import streamlit as st
from utils import download_and_display_file
from views.tasks import tasks as list_tasks


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
    st.markdown(
        f"Are you sure you want to delete the file:\n  **{os.path.basename(file)}**?\n   This action cannot be undone."
    )
    if st.button("Delete 🗑️", use_container_width=True):
        resulst = requests.delete(f"http://back:80/files/delete/{file}")
        if resulst.status_code == 200:
            st.success("File deleted successfully.")
            del st.session_state.file_to_see
            st.rerun()
        else:
            st.error("Failed to delete the file. Please try again.")


def see_file(file):
    date = file.split("/")[2]
    subfolder = file.split("/")[3]
    file_name = os.path.basename(file)
    file_extension = os.path.splitext(file_name)[1].lower().replace(".", "")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📥",
            f"http://back:80/files/download/{file}",
            file_name=file_name,
            help="Click to download the file.",
            use_container_width=True,
            key=f"see_download_{file}",
        )
    with col2:
        if st.button(
            "🗑️",
            use_container_width=True,
            help="Click to delete the file.",
            key=f"see_delete_{file}",
        ):
            dialog_delete_file(file)

    tab_details, tab_summarize, tab_metadata, tab_notes, tab_tasks = st.tabs(
        ["Détails", "Summarize", "Metadata", "Notes", "Tasks"]
    )
    with tab_details:
        st.markdown(f"#### {file_name}")
        st.caption(f"**Date:** {date}")
        st.caption(f"**Subfolder:** {subfolder}")
        st.caption(f"**Path:** {file}")
    with tab_summarize:
        result = requests.get(f"http://back:80/summarization/get/{file}")
        if result.status_code != 200:
            st.info(
                "No summary available for this file. You can create a summary by clicking the button below."
            )
            if st.button(
                "Create summary",
                use_container_width=True,
                help="Click to create a summary for this file.",
            ):
                result = requests.post(f"http://back:80/summarization/ask/{file}")
                if result.status_code == 200:
                    st.success("Task for summarization created.")
                    st.rerun()
                else:
                    st.error("Failed to ask summary.")
        else:
            st.text(
                "Summarization",
                value=result.content.decode("utf-8"),
                height=300,
                help="This is the summary of the file.",
            )
    with tab_tasks:
        list_tasks(
            file,
            list_ocr=True
            if file_extension == "png"
            or file_extension == "jpg"
            or file_extension == "jpeg"
            or file_extension == "bmp"
            or file_extension == "webp"
            else False,
            list_transcription=True
            if file_extension == "mp3" or file_extension == "wav"
            else False,
            print_errors=False,
        )


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
            st.divider()
            see_file(st.session_state.file_to_see)

        with cols[1]:
            with st.container(border=True):
                download_and_display_file(st.session_state.file_to_see)
                file_extension = (
                    os.path.splitext(st.session_state.file_to_see)[1]
                    .lower()
                    .replace(".", "")
                )
                if (
                    file_extension == "mp4"
                    or file_extension == "wav"
                    or file_extension == "mov"
                ):
                    with st.spinner("Loading transcription..."):
                        result = requests.get(
                            f"http://back:80/transcription/get/{st.session_state.file_to_see}"
                        )
                    if result.status_code == 200:
                        st.markdown("### Transcription")
                        st.code(
                            result.json().get("transcription", ""),
                            language="plaintext",
                        )
                    else:
                        st.error(
                            "Failed to load transcription. Please try again later."
                        )
                        if st.button("Start transcription", use_container_width=True):
                            result = requests.post(
                                f"http://back:80/transcription/ask/{st.session_state.file_to_see}",
                            )
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
