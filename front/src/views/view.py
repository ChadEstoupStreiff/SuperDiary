import datetime
import mimetypes
import os
from typing import List

import requests
import streamlit as st
from pages import PAGE_EXPLORER
from utils import (
    clear_cache,
    download_and_display_file,
    generate_tag_visual_markdown,
    generate_project_visual_markdown,
    toast_for_rerun,
)
from views.settings import tasks as list_tasks


@st.dialog("🗑️ Delete file")
def dialog_delete_file(file):
    # MARK: DELETE FILE
    """
    This dialog is used to confirm the deletion of a file.
    It provides a button to delete the file and a button to cancel the action.
    """
    st.markdown(
        f"Are you sure you want to delete the file:\n  **{os.path.basename(file)}**?\n This action cannot be undone."
    )
    if st.button("Delete 🗑️", use_container_width=True):
        resulst = requests.delete(f"http://back:80/files/delete/{file}")
        if resulst.status_code == 200:
            toast_for_rerun(
                "File deleted successfully.",
                icon="🗑️",
            )
            clear_cache()
            st.rerun()
        else:
            st.error("Failed to delete the file. Please try again.")

@st.dialog("✏️ Edit file details")
def dialog_edit_file(file: str, projects: List[str], tags: List[str]):
    # MARK: EDIT FILE DETAILS
    """
    This dialog is used to edit the details of a file.
    It provides fields to edit the file name, subfolder, and date.
    """
    file_name = os.path.basename(file)
    date = file.split("/")[2]
    subfolder = file.split("/")[3]
    st.markdown(f"Edit details for file: **{file_name}**")

    new_name = st.text_input(
        "File Name",
        value=file_name,
        help="Enter the new name for the file.",
    )
    new_date = st.date_input(
        "Date",
        value=datetime.datetime.strptime(date, "%Y-%m-%d").date(),
        help="Select the new date for the file.",
    ).strftime("%Y-%m-%d")

    if new_name != file_name:
        st.warning(
            f"You are about to change the file name to {new_name}. This action cannot be undone."
        )
    if new_date != date:
        st.warning(
            f"You are about to change the date to {new_date}. This action cannot be undone."
        )
    if st.button("Save Changes", use_container_width=True):
        if new_name != file_name or new_date != date:
            result_move = requests.post(
                f"http://back:80/files/move/{file}?name={new_name}&date={new_date}&subfolder={subfolder}",
            )
            if result_move.status_code != 200:
                st.error(
                    "Failed to update file details. Please check the file name and date."
                )
                return
        toast_for_rerun(
            "File details updated successfully.",
            icon="✅",
        )
        clear_cache()
        st.session_state["file_to_see"] = (
            "/shared/" + new_date + "/" + subfolder + "/" + new_name
        )
        st.rerun()
    st.divider()

    all_projects = [
        p for p in requests.get("http://back:80/projects").json() if p not in projects
    ]
    all_tags = [t for t in requests.get("http://back:80/tags").json() if t not in tags]

    st.markdown("### Projects")
    if len(projects) == 0:
        st.info("This file is not associated with any project.")
    else:
        for project in projects:
            cols = st.columns([1, 3])
            with cols[0]:
                if st.button(
                    "Remove",
                    key=f"remove_project_{project['name']}",
                    help=f"Click to remove the project {project['name']} from this file.",
                    use_container_width=True,
                ):
                    requests.delete(
                        f"http://back:80/project/{project['name']}/file?file={file}"
                    )
                    toast_for_rerun(
                        "Project removed successfully.",
                        icon="🗑️",
                    )
                    st.rerun()
            with cols[1]:
                st.markdown(
                    generate_project_visual_markdown(project["name"], project["color"]),
                    unsafe_allow_html=True,
                )

    new_project = st.selectbox(
        "Add to project",
        options=all_projects,
        format_func=lambda x: x["name"],
        key="add_project",
        help="Select a project to add this file to.",
    )
    if st.button(
        "Add Project",
        use_container_width=True,
        help="Click to add the selected project to this file.",
    ):
        result_add = requests.post(
            f"http://back:80/project/{new_project['name']}/file?file={file}",
        )
        if result_add.status_code == 200:
            toast_for_rerun(
                "Project added successfully.",
                icon="✅",
            )
            st.rerun()
        else:
            st.error("Failed to add project. Please try again.")

    st.markdown("### Tags")
    if len(tags) == 0:
        st.info("This file is not associated with any tags.")
    else:
        for tag in tags:
            cols = st.columns([1, 3])
            with cols[0]:
                if st.button(
                    "Remove",
                    key=f"remove_tag_{tag['name']}",
                    help=f"Click to remove the tag {tag['name']} from this file.",
                    use_container_width=True,
                ):
                    requests.delete(
                        f"http://back:80/tag/{tag['name']}/file?file={file}"
                    )
                    toast_for_rerun(
                        "Tag removed successfully.",
                        icon="🗑️",
                    )
                    st.rerun()
            with cols[1]:
                st.markdown(
                    generate_tag_visual_markdown(tag["name"], tag["color"]),
                    unsafe_allow_html=True,
                )
    new_tag = st.selectbox(
        "Add Tag",
        options=all_tags,
        format_func=lambda x: x["name"],
        key="add_tag",
        help="Select a tag to add to this file.",
    )
    if st.button(
        "Add Tag",
        use_container_width=True,
        help="Click to add the selected tag to this file.",
    ):
        result_add = requests.post(
            f"http://back:80/tag/{new_tag['name']}/file?file={file}",
        )
        if result_add.status_code == 200:
            toast_for_rerun(
                "Tag added successfully.",
                icon="✅",
            )
            st.rerun()
        else:
            st.error("Failed to add tag. Please try again.")


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
    # MARK: DETAILS
    with tab_details:
        st.markdown(f"### {file_name}")
        st.caption(f"**Date:** {date}")
        st.caption(f"**Subfolder:** {subfolder}")
        st.caption(f"**Path:** {file}")

        projects = requests.get(f"http://back:80/projects_of/{file}")
        if projects.status_code == 200:
            projects = projects.json()
        else:
            projects = []
        tags = requests.get(f"http://back:80/tags_of/{file}")
        if tags.status_code == 200:
            tags = tags.json()
        else:
            tags = []

        st.markdown("##### Projects")
        if len(projects) == 0:
            st.info("This file is not associated with any project.")
        else:
            for project in projects:
                st.markdown(
                    generate_project_visual_markdown(project["name"], project["color"]),
                    unsafe_allow_html=True,
                )

        st.markdown("##### Tags")
        if len(tags) == 0:
            st.info("This file is not associated with any tags.")
        else:
            for tag in tags:
                st.markdown(
                    generate_tag_visual_markdown(tag["name"], tag["color"]),
                    unsafe_allow_html=True,
                )

        if st.button("Edit file details", use_container_width=True):
            dialog_edit_file(file, projects=projects, tags=tags)

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
                    toast_for_rerun(
                        "Summary task created successfully. It may take some time to process.",
                        icon="✅",
                    )
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
                    st.toast(
                        "Notes updated successfully.",
                        icon="✅",
                    )
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
        # st.error("No file selected to view. Please select a file from the explorer.")
        st.switch_page(PAGE_EXPLORER)
        return
    file = st.session_state.file_to_see

    cols = st.columns(2)
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
            with st.spinner("Downloading file..."):
                download_and_display_file(file)
            mime, _ = mimetypes.guess_type(file)
            if mime is None:
                st.error("Could not determine the file type. Please check the file.")

            elif mime.startswith("audio/") or mime.startswith("video/"):
                with st.spinner("Loading transcription..."):
                    result = requests.get(f"http://back:80/transcription/get/{file}")
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
                            toast_for_rerun(
                                "Transcription task created successfully. It may take some time to process.",
                                icon="✅",
                            )
                            st.rerun()
                        else:
                            st.error("Failed to create transcription task.")

            elif mime.startswith("image/"):
                with st.spinner("Loading OCR..."):
                    result = requests.get(f"http://back:80/ocr/get/{file}")
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
                            toast_for_rerun(
                                "OCR task created successfully. It may take some time to process.",
                                icon="✅",
                            )
                            st.rerun()
                        else:
                            st.error("Failed to create OCR task.")


if __name__ == "__main__":
    view()
