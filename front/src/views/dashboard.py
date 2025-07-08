import datetime
import json

import requests
import streamlit as st
from core.files import display_files
from utils import clear_cache, toast_for_rerun


@st.dialog("📤 Upload files")
def dialog_upload(files):
    toggle_edit_date = st.toggle(
        "Edit Date By file",
        value=False,
        help="Enable to edit the date of the files being uploaded.",
    )
    top_date = st.container()
    if not toggle_edit_date:
        date = st.date_input(
            "Upload Date",
            help="Select the date for the files being uploaded.",
        )

    file_edit_info = {}
    with top_date:
        for file in files:
            if file.name not in file_edit_info:
                file_edit_info[file.name] = {}

            with st.container(
                border=True,
                key=f"file_container_{file.name}",
            ):
                cols = st.columns([5, 2] if toggle_edit_date else [1])
                with cols[0]:
                    file_edit_info[file.name]["name"] = st.text_input(
                        f"Save {file.name} as",
                        value=file.name,
                        help=f"Enter the name to save {file.name} as.",
                        key=f"file_name_{file.name}",
                    )
                if toggle_edit_date:
                    with cols[1]:
                        file_edit_info[file.name]["date"] = st.date_input(
                            "Edit date",
                            help=f"Select the date for {file.name}.",
                            key=f"file_date_{file.name}",
                        ).strftime("%Y-%m-%d")

    if st.button(
        "✅ Save files",
        help="Click to upload the selected files.",
        use_container_width=True,
    ):
        with st.spinner("Saving files...", show_time=True):
            files_payload = [("files", (file.name, file, file.type)) for file in files]
            request = f"http://back:80/files/upload?subdirectory=uploads&file_edit_info={json.dumps(file_edit_info)}"
            if not toggle_edit_date:
                request += f"&date={date.strftime('%Y-%m-%d')}"
            response = requests.post(
                request,
                files=files_payload,
            )
            if response.status_code == 200:
                del st.session_state.dashboard_new_files
                clear_cache()
                toast_for_rerun(
                    "Files uploaded successfully!",
                    icon="🆕",
                )
                st.rerun()
            else:
                st.error(f"Failed to upload files: {response.text}")
                st.toast(f"Failed to upload files: {response.text}", icon="❌")


def dashboard():
    """
    Render the dashboard page.
    """
    st.write("Welcome to the Super Diary Dashboard!")
    cols = st.columns([2, 1])

    with cols[1]:

        def on_change_files():
            st.session_state.dashboard_new_files = True

        files = st.file_uploader(
            "Upload files",
            accept_multiple_files=True,
            on_change=on_change_files,
            help="Upload files to be processed by the system.",
        )
        if (
            files
            and "dashboard_new_files" in st.session_state
            and st.session_state.dashboard_new_files
        ):
            dialog_upload(files)

        with st.container(border=True):
            metric_cols = st.columns(2)
            with metric_cols[0]:
                st.metric(
                    label="Total Files",
                    value=requests.get("http://back:80/files/count").json(),
                    help="Total number of files processed by the system.",
                )
            with metric_cols[1]:
                st.metric(
                    label="Total Projects",
                    value=len(requests.get("http://back:80/projects").json()),
                    help="Total number of projects created in the system.",
                )
                st.metric(
                    label="Total Tags",
                    value=len(requests.get("http://back:80/tags").json()),
                    help="Total number of tags created in the system.",
                )

    with cols[0]:
        today = datetime.date.today()

        with st.expander("Added files", expanded=True):
            st.error("In dev...")

        with st.expander("Opened files", expanded=True):
            st.error("In dev...")

        today_files = requests.get(
            f"http://back:80/files/search?start_date={today}&end_date={today}"
        ).json()
        with st.expander(f"Today files - {len(today_files)} files", expanded=True):
            display_files(
                today_files,
                representation_mode=0,
                key="today_files",
            )

        week_files = requests.get(
            f"http://back:80/files/search?start_date={today - datetime.timedelta(days=7)}&end_date={today}"
        ).json()
        with st.expander(f"Week files (7d) - {len(week_files)} files", expanded=True):
            display_files(
                week_files,
                representation_mode=0,
                key="week_files",
            )


if __name__ == "__main__":
    dashboard()
