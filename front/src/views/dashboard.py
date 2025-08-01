import datetime
import json

import requests
import streamlit as st
from core.files import display_files
from utils import clear_cache, toast_for_rerun


@st.dialog("📤 Upload files", width="large")
def dialog_upload(files):
    cols = st.columns(3)
    with cols[0]:
        toggle_edit_date = st.toggle(
            "Edit Date By file",
            value=False,
            help="Enable to edit the date of the files being uploaded.",
        )
    with cols[1]:
        toggle_per_file_projects = st.toggle(
            "Edit Projects By file",
            value=False,
            help="Enable to edit the projects associated with each file.",
        )
    with cols[2]:
        toggle_per_file_tags = st.toggle(
            "Edit Tags By file",
            value=False,
            help="Enable to edit the tags associated with each file.",
        )

    if not toggle_edit_date:
        date = st.date_input(
            "Upload Date",
            help="Select the date for the files being uploaded.",
        )
    projects = requests.get("http://back:80/projects").json()
    tags = requests.get("http://back:80/tags").json()

    cols = st.columns(2)
    with cols[0]:
        selected_projects = st.multiselect(
            "Select Projects",
            options=[p["name"] for p in projects],
            help="Select the projects to associate with the uploaded files.",
        )
    with cols[1]:
        selected_tags = st.multiselect(
            "Select Tags",
            options=[t["name"] for t in tags],
            help="Select the tags to associate with the uploaded files.",
        )

    file_edit_info = {}
    rest_projects = [p for p in projects if p["name"] not in selected_projects]
    rest_tags = [t for t in tags if t["name"] not in selected_tags]
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
            if toggle_per_file_projects or toggle_per_file_tags:
                cols = st.columns(2)
                with cols[0]:
                    if toggle_per_file_projects:
                        file_edit_info[file.name]["projects"] = st.multiselect(
                            "Projects",
                            options=[p["name"] for p in rest_projects],
                            help=f"Select projects for {file.name}.",
                            key=f"file_projects_{file.name}",
                        )
                with cols[1]:
                    if toggle_per_file_tags:
                        file_edit_info[file.name]["tags"] = st.multiselect(
                            "Tags",
                            options=[t["name"] for t in rest_tags],
                            help=f"Select tags for {file.name}.",
                            key=f"file_tags_{file.name}",
                        )

    if st.button(
        "✅ Save files",
        help="Click to upload the selected files.",
        use_container_width=True,
    ):
        with st.spinner("Saving files...", show_time=True):
            files_payload = [("files", (file.name, file, file.type)) for file in files]
            request = f"http://back:80/files/upload?subdirectory=uploads&file_edit_info={json.dumps(file_edit_info)}&projects={json.dumps(selected_projects)}&tags={json.dumps(selected_tags)}"
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

        sub_cols = st.columns(2)
        with sub_cols[0]:
            added_files = requests.get("http://back:80/stockpile/recentadded").json()
            with st.expander("Added files", expanded=True):
                display_files(
                    added_files,
                    representation_mode=0,
                    key="recent_added_files",
                )

        with sub_cols[1]:
            opened_files = requests.get("http://back:80/stockpile/recentopened").json()
            with st.expander("Opened files", expanded=True):
                display_files(
                    opened_files,
                    representation_mode=0,
                    key="recent_opened_files",
                )

        sub_cols = st.columns(2)
        with sub_cols[0]:
            today_files = requests.get(
                f"http://back:80/files/search?start_date={today}&end_date={today}"
            ).json()
            with st.expander(f"Today files - {len(today_files)} files", expanded=True):
                display_files(
                    today_files,
                    representation_mode=0,
                    key="today_files",
                )

        with sub_cols[1]:
            week_files = requests.get(
                f"http://back:80/files/search?start_date={today - datetime.timedelta(days=7)}&end_date={today}"
            ).json()
            with st.expander(
                f"Week files (7d) - {len(week_files)} files", expanded=True
            ):
                display_files(
                    week_files,
                    representation_mode=0,
                    key="week_files",
                )


if __name__ == "__main__":
    dashboard()
