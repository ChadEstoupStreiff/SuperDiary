import datetime
import json
import tempfile
from pathlib import Path

import requests
import streamlit as st
from utils import clear_cache


def clear_selected_note():
    if "notes_content" in st.session_state:
        del st.session_state["notes_name"]
        del st.session_state["notes_content"]


def notes():
    # MARK: LOADING
    with st.sidebar:
        note_date = st.date_input(
            "Notes of",
            help="Choose the date for the notes.",
            key="notes_date",
            on_change=clear_selected_note,
        )

        notes_list = [
            n.split("/")[-1]
            for n in requests.get(
                f"http://back:80/files/search?subfolder=notes&start_date={note_date}&end_date={note_date}"
            ).json()
        ]

        with st.container(border=True):
            if st.button("Create new note", use_container_width=True):
                new_note_name = (
                    datetime.datetime.now().strftime("%H-%M-%S") + " - New note"
                )
                notes_list.append(new_note_name)
                st.session_state["notes_name"] = new_note_name
                st.session_state["notes_content"] = "# 🚀 New note"
                st.toast(
                    f"Note '{new_note_name}' created successfully.",
                    icon="✅",
                )
                clear_cache()

            selected_note = st.selectbox(
                "Select a note to view or edit",
                notes_list,
                key="notes_selectbox",
                help="Choose a note from the list to view or edit its content.",
                on_change=clear_selected_note,
            )

        if "notes_content" not in st.session_state and selected_note:
            with st.spinner("Loading note..."):
                st.session_state["notes_name"] = selected_note
                # TODO downloading the note content
                st.session_state["notes_content"] = "# 🚀 New note"

    if "notes_content" in st.session_state and "notes_name" in st.session_state:
        selected_note = st.session_state["notes_name"]
        # MARK: SETTINGS
        with st.sidebar:
            side_by_side = st.checkbox("Side by Side", value=True)
            if side_by_side:
                editor_size = st.number_input(
                    "Editor height (px)",
                    min_value=300,
                    max_value=1800,
                    value=700,
                    step=50,
                    help="Set the height of the editor in pixels.",
                )
            st.divider()
            st.info(f"Editing: {selected_note}")

        cols = st.columns(2 if side_by_side else 1)

        # MARK: CONTENT
        with cols[0]:
            markdown_input = st.text_area(
                "Edit note content",
                value=st.session_state["notes_content"],
                height=editor_size if side_by_side else None,
                key=f"notes_textarea_{selected_note}",
            )

        with cols[1 if side_by_side else 0]:
            st.caption("Preview")
            with st.container(
                border=True, height=editor_size if side_by_side else None
            ):
                st.markdown(markdown_input, unsafe_allow_html=False)

        # MARK: SAVE
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
