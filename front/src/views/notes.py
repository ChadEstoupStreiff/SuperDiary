import datetime
import json
import tempfile
from pathlib import Path

import requests
import streamlit as st
from pages import PAGE_VIEWER
from utils import clear_cache, toast_for_rerun


def clear_selected_note():
    if "notes_content" in st.session_state:
        del st.session_state["notes_name"]
        del st.session_state["notes_content"]


def notes():
    # MARK: LOADING
    with st.sidebar:
        with st.container(border=True):
            st.subheader("Load a note")
            note_date = st.date_input(
                "Notes of",
                help="Choose the date for the notes.",
                key="notes_date",
            )

            with st.container(border=True):
                if st.button("Create new note", use_container_width=True):
                    clear_cache()
                    new_note_name = datetime.datetime.now().strftime("%H-%M-%S")
                    st.session_state["notes_name"] = f"/shared/{note_date}/notes/{new_note_name}.md"
                    st.session_state["notes_content"] = "# 🚀 New note"
                    st.toast(
                        f"Note '{new_note_name}' created successfully.",
                        icon="✅",
                    )

                selected_note = st.selectbox(
                    "Select a note to view or edit",
                    [
                n.split("/")[-1]
                for n in requests.get(
                    f"http://back:80/files/search?subfolder=notes&start_date={note_date}&end_date={note_date}"
                ).json()
            ],
                    key="notes_selectbox",
                    help="Choose a note from the list to view or edit its content.",
                    on_change=clear_selected_note,
                )

    if "notes_content" not in st.session_state and selected_note:
        with st.spinner("Loading note..."):
            file = f"/shared/{note_date}/notes/{selected_note}"
            st.session_state["notes_name"] = file
            note_content = requests.get(f"http://back:80/files/download/{file}")
            if note_content.status_code == 200:
                st.toast(
                    f"Note '{selected_note}' loaded successfully.",
                    icon="✅",
                )
                st.session_state["notes_content"] = note_content.text
            else:
                st.session_state["notes_content"] = "# 🚀 New note"
                st.toast(
                    f"Note '{selected_note}' not found. Starting with a new note.",
                    icon="❌",
                )

    if "notes_content" in st.session_state and "notes_name" in st.session_state:
        selected_note = st.session_state["notes_name"]
        note_name = selected_note.split("/")[-1]
        # MARK: SETTINGS
        with st.sidebar:
            side_by_side = st.toggle("Side by Side", value=True)
            if side_by_side:
                editor_size = st.number_input(
                    "Editor height (px)",
                    min_value=300,
                    max_value=1800,
                    value=1100,
                    step=50,
                    help="Set the height of the editor in pixels.",
                )
            st.divider()
            st.info(f"Editing: {selected_note}")

            new_name = st.text_input(
                "Note name",
                value=note_name,
                help="Enter a new name for the note.",
                key="notes_rename_input",
            )
            if new_name != note_name:
                result = requests.post(
                    f"http://back:80/files/move/{selected_note}?name={new_name}",
                )
                if result.status_code == 200:
                    st.session_state["notes_name"] = f"/shared/{note_date}/notes/{new_name}"
                    toast_for_rerun(
                        f"Note renamed to '{new_name}'.",
                        icon="✅",
                    )
                    st.rerun()
                else:
                    st.error(f"Failed to rename note: {result.text}")
                    st.toast(
                        f"Failed to rename note: {result.text}",
                        icon="❌",
                    )

            if st.button(
                "🔎 Open file",
                use_container_width=True,
                key="notes_viewer_button",
            ):
                st.session_state.file_to_see = selected_note
                st.switch_page(PAGE_VIEWER)

        cols = st.columns(2 if side_by_side else 1)

        # MARK: CONTENT
        with cols[0]:
            markdown_input = st.text_area(
                "Edit note content",
                value=st.session_state["notes_content"],
                height=editor_size if side_by_side else None,
                key=f"notes_textarea_{selected_note}",
                label_visibility="hidden",
            )

        with cols[1 if side_by_side else 0]:
            with st.container(
                border=True, height=editor_size + 50 if side_by_side else None
            ):
                st.markdown(markdown_input, unsafe_allow_html=False)

        # MARK: SAVE
        if st.session_state["notes_content"] != markdown_input:
            with st.sidebar:
                with tempfile.NamedTemporaryFile(
                    mode="w+", delete=True, suffix=".md"
                ) as tmpfile:
                    tmpfile.write(markdown_input)
                    tmpfile.flush()
                    tmpfile.seek(0)
                    tmpfile_path = tmpfile.name

                    # Construct file_edit_info automatically
                    file_edit_info = {
                        selected_note: {
                            "name": Path(selected_note).stem + ".md",
                            "date": note_date.strftime("%Y-%m-%d"),
                        }
                    }

                    with open(tmpfile_path, "rb") as f:
                        files_payload = [("files", (selected_note, f, "text/markdown"))]
                        query = (
                            f"http://back:80/files/upload?subdirectory=notes"
                            f"&file_edit_info={json.dumps(file_edit_info)}"
                            f"&date={note_date}"
                        )

                        response = requests.post(query, files=files_payload)

                    actual_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if response.status_code == 200:
                        st.toast(
                            f"Note '{selected_note}' saved successfully at {actual_date}.",
                            icon="✅",
                        )
                    else:
                        st.toast(
                            f"Failed to save note '{selected_note}' at {actual_date}.",
                            icon="❌",
                        )


if __name__ == "__main__":
    notes()
