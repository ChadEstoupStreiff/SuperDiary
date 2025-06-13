import datetime
import mimetypes
import os
import time

import requests
import streamlit as st
from utils import download_and_display_file
from views.tasks import tasks as list_tasks
from pages import PAGE_EXPLORER


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
    mime, _ = mimetypes.guess_type(file)

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
        if result.status_code == 200 and result.json() is not None:
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
                    time.sleep(1)
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
        if result.status_code == 200 and result.json() is not None:
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
            list_ocr=True if mime.startswith("image/") else False,
            list_transcription=True
            if mime.startswith("audio/") or mime.startswith("video/")
            else False,
        )


def view():
    if "file_to_see" not in st.session_state:
        st.error("No file selected to view. Please select a file from the explorer.")
        return
    file = st.session_state.file_to_see

    cols = st.columns([1, 2])
    with cols[0]:
        # if st.button(
        #     "🔙 Back to Explorer",
        #     on_click=lambda: st.session_state.pop("file_to_see", None),
        #     use_container_width=True,
        #     key="back_to_explorer",
        # ):
        #     st.switch_page(PAGE_EXPLORER)
        see_file(file)

    with cols[1]:
        with st.container(border=True):
            download_and_display_file(file)
            mime, _ = mimetypes.guess_type(file)
            if mime.startswith("audio/") or mime.startswith("video/"):
                with st.spinner("Loading transcription..."):
                    result = requests.get(
                        f"http://back:80/transcription/get/{file}"
                    )
                if result.status_code == 200 and result.json() is not None:
                    st.subheader("Transcription")
                    st.write(result.json().get("transcription", ""))
                else:
                    st.error("Failed to load transcription. Please try again later.")
                    if st.button("Start transcription", use_container_width=True):
                        result = requests.post(
                            f"http://back:80/transcription/ask/{file}",
                        )
                        if result.status_code == 200:
                            st.success("Transcription task created.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to create transcription task.")

            elif mime.startswith("image/"):
                with st.spinner("Loading OCR..."):
                    result = requests.get(
                        f"http://back:80/ocr/get/{file}"
                    )
                if result.status_code == 200 and result.json() is not None:
                    st.subheader("OCR")
                    st.write(result.json().get("ocr", ""))
                else:
                    st.error("Failed to load OCR. Please try again later.")
                    if st.button("Start OCR", use_container_width=True):
                        result = requests.post(
                            f"http://back:80/ocr/ask/{file}",
                        )
                        if result.status_code == 200:
                            st.success("OCR task created.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to create OCR task.")


if __name__ == "__main__":
    view()
