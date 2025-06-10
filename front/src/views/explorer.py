import datetime
import os
import time

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
    # MARK: DELETE FILE
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
    # MARK: SEE FILE
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

    # MARK: SUMMARIZE
    with tab_summarize:
        result = requests.get(f"http://back:80/summarize/get/{file}")
        if result.status_code == 200:
            summary = result.json().get("summary", "")
            keywords = result.json().get("keywords", [])
            st.caption(f"Keywords : {', '.join(keywords)}")
            with st.container(border=True):
                st.text(summary)
        else:
            st.info(
                "No summary available for this file. You can create a summary by clicking the button below."
            )
            if st.button(
                "Create summary",
                use_container_width=True,
                help="Click to create a summary for this file.",
            ):
                result = requests.post(f"http://back:80/summarize/ask/{file}")
                if result.status_code == 200:
                    st.success("Task for summarization created.")
                    st.rerun()
                else:
                    st.error("Failed to ask summary.")

    # MARK: METADATA
    with tab_metadata:
        result = requests.get(f"http://back:80/files/metadata/{file}")
        if result.status_code == 200:
            metadata = result.json()
            size = metadata.get("size", 0) / (1024 * 1024)
            date_created = datetime.datetime.fromisoformat(
                metadata.get("created", 0)
            ).strftime("%Y-%m-%d %H:%M:%S")
            date_modified = datetime.datetime.fromisoformat(
                metadata.get("modified", 0)
            ).strftime("%Y-%m-%d %H:%M:%S")
            path = metadata.get("path", "Unknown")
            mime = metadata.get("mime_type", "Unknown")

            st.markdown(f"**Size:** {size:.3f} Mb")
            st.markdown(f"**Created on:** {date_created}")
            st.markdown(f"**Modified on:** {date_modified}")
            st.markdown(f"**Path:** {path}")
            st.markdown(f"**MIME Type:** {mime}")
        else:
            st.error("Failed to load metadata for this file.")

    # MARK: NOTES
    with tab_notes:
        result = requests.get(f"http://back:80/notes/{file}")
        if result.status_code == 200:
            notes = result.json().get("note", "")
            edited_notes = st.text_area(
                "Notes",
                value=notes,
                height=500,
                help="These are the notes for the file. They are used in search context and can be edited.",
            )
            if edited_notes != notes:
                result_update = requests.post(
                    f"http://back:80/notes/{file}?note={edited_notes}"
                )
                if result_update.status_code == 200:
                    st.success("Notes updated successfully.")
                else:
                    st.error("Failed to update notes. Please try again later.")
        else:
            st.error("Failed to load notes for this file.")

    # MARK: TASKS
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
            if file_extension == "mp3"
            or file_extension == "wav"
            or file_extension == "mp4"
            or file_extension == "avi"
            or file_extension == "mov"
            else False,
            print_errors=False,
        )


def explorer():
    """
    This function serves as a placeholder for the explorer view.
    It currently does not perform any operations or return any data.
    """
    if "file_to_see" in st.session_state:
        # MARK: FILE TO SEE
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
                    file_extension == "mp3"
                    or file_extension == "wav"
                    or file_extension == "mp4"
                    or file_extension == "avi"
                    or file_extension == "mov"
                ):
                    with st.spinner("Loading transcription..."):
                        result = requests.get(
                            f"http://back:80/transcription/get/{st.session_state.file_to_see}"
                        )
                    if result.status_code == 200:
                        st.subheader("Transcription")
                        st.write(result.json().get("transcription", ""))
                    else:
                        st.error(
                            "Failed to load transcription. Please try again later."
                        )
                        if st.button("Start transcription", use_container_width=True):
                            result = requests.post(
                                f"http://back:80/transcription/ask/{st.session_state.file_to_see}",
                            )
                            if result.status_code == 200:
                                st.success("Transcription task created.")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to create transcription task.")

                if (
                    file_extension == "png"
                    or file_extension == "jpg"
                    or file_extension == "jpeg"
                    or file_extension == "bmp"
                    or file_extension == "webp"
                ):
                    with st.spinner("Loading OCR..."):
                        result = requests.get(
                            f"http://back:80/ocr/get/{st.session_state.file_to_see}"
                        )
                    if result.status_code == 200:
                        st.subheader("OCR")
                        st.write(result.json().get("ocr", ""))
                    else:
                        st.error("Failed to load OCR. Please try again later.")
                        if st.button("Start OCR", use_container_width=True):
                            result = requests.post(
                                f"http://back:80/ocr/ask/{st.session_state.file_to_see}",
                            )
                            if result.status_code == 200:
                                st.success("OCR task created.")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to create OCR task.")
    else:
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
                    download_and_display_file(files[i])
        else:
            st.write("No files found in the system.")
