import os

import pandas as pd
import requests
import streamlit as st
from pages import PAGE_VIEWER
from utils import (
    download_and_display_file,
    generate_aside_project_markdown,
    generate_aside_tag_markdown,
)


def box_file(file: str, height: int, show_preview: bool, key: str = ""):
    # MARK: BOX FILE
    with st.container(border=True, height=height):
        preview = None
        if show_preview:
            preview = st.container(
                border=True,
                height=height // 2,
            )
        file_name = os.path.basename(file)
        date = file.split("/")[2]
        subfolder = file.split("/")[3]

        cols = st.columns(2)
        st.markdown(f"##### {file_name}")
        st.caption(
            f"**📅 Date:** {date}<br/>**📁 Subfolder:** {subfolder}",
            unsafe_allow_html=True,
        )
        projects = requests.get(f"http://back:80/projects_of/{file}").json()
        tags = requests.get(f"http://back:80/tags_of/{file}").json()
        if projects:
            st.markdown(
                generate_aside_project_markdown(
                    [p["name"] for p in projects],
                    [p["color"] for p in projects],
                ),
                unsafe_allow_html=True,
            )
        if tags:
            st.markdown(
                generate_aside_tag_markdown(
                    [t["name"] for t in tags],
                    [t["color"] for t in tags],
                ),
                unsafe_allow_html=True,
            )

        with cols[0]:
            if st.button(
                "🔎",
                help="Click to view file details.",
                use_container_width=True,
                key=f"{key}_view_{file}",
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
                key=f"{key}_download_{file}",
            )
    return preview


def line_file(file: str, show_preview: bool, key: str = ""):
    MAX_SUMMARY_LENGTH = 500

    # MARK: LINE FILE
    with st.container(border=True):
        file_name = os.path.basename(file)
        date = file.split("/")[2]
        subfolder = file.split("/")[3]

        cols = st.columns([2, 2, 3, 1] if show_preview else [2, 3, 1])
        with cols[1 if show_preview else 0]:
            st.markdown(f"#### {file_name}")
            st.caption(
                f"**📅 Date:** {date}<br/>**📁 Subfolder:** {subfolder}",
                unsafe_allow_html=True,
            )
            projects = requests.get(f"http://back:80/projects_of/{file}").json()
            tags = requests.get(f"http://back:80/tags_of/{file}").json()
            if projects:
                st.markdown(
                    generate_aside_project_markdown(
                        [p["name"] for p in projects],
                        [p["color"] for p in projects],
                    ),
                    unsafe_allow_html=True,
                )
            if tags:
                st.markdown(
                    generate_aside_tag_markdown(
                        [t["name"] for t in tags],
                        [t["color"] for t in tags],
                    ),
                    unsafe_allow_html=True,
                )
        with cols[2 if show_preview else 1]:
            result = requests.get(f"http://back:80/summarize/get/{file}")
            if result.status_code == 200 and result.json() is not None:
                summary = result.json().get("summary", "")
                keywords = result.json().get("keywords", [])
                st.caption(f"Keywords : {', '.join(keywords)}")
                with st.container(border=True):
                    st.text(
                        summary[:MAX_SUMMARY_LENGTH]
                        + (" ..." if len(summary) > MAX_SUMMARY_LENGTH else "")
                    )
            else:
                st.info("No summary available for this file.")
        with cols[3 if show_preview else 2]:
            if st.button(
                "🔎",
                help="Click to view file details.",
                use_container_width=True,
                key=f"{key}_view_{file}",
            ):
                st.session_state.file_to_see = file
                st.switch_page(PAGE_VIEWER)
            st.download_button(
                "📥",
                f"http://back:80/files/download/{file}",
                file_name=file_name,
                help="Click to download the file.",
                use_container_width=True,
                key=f"{key}_download_{file}",
            )
        if show_preview:
            return cols[0].container(
                border=True,
                height=300,
            )
        return None


def display_files(
    files,
    representation_mode: int,
    show_preview: bool = False,
    nbr_of_files_per_line: int = 3,
    key="",
):
    if len(files) == 0:
        st.info("No files found.")
    elif representation_mode == 0:
        table = pd.DataFrame(
            [
                {
                    "see": False,
                    "File": os.path.basename(file),
                    "Date": file.split("/")[2],
                    "Subfolder": file.split("/")[3],
                    "Projects": ", ".join(
                        [
                            p["name"]
                            for p in requests.get(
                                f"http://back:80/projects_of/{file}"
                            ).json()
                        ]
                    ),
                    "Tags": ", ".join(
                        [
                            t["name"]
                            for t in requests.get(
                                f"http://back:80/tags_of/{file}"
                            ).json()
                        ]
                    ),
                }
                for file in files
            ]
        )
        table = st.data_editor(
            table,
            column_config={
                "see": st.column_config.CheckboxColumn(
                    "🔎",
                    default=False,
                )
            },
            use_container_width=True,
            hide_index=True,
            disabled=["File", "Date", "Subfolder", "Path"],
            key=f"{key}_lines",
        )
        selected_rows = table.query("see == True")
        if len(selected_rows) > 0:
            st.session_state.file_to_see = selected_rows.iloc[0]["Path"]
            st.switch_page(PAGE_VIEWER)

    # MARK: BOXES
    elif representation_mode == 1:
        cols = st.columns(nbr_of_files_per_line)
        file_preview_infos = []
        for i, file in enumerate(files):
            with cols[i % nbr_of_files_per_line]:
                file_preview_infos.append(
                    box_file(
                        file,
                        height=600 if show_preview else 300,
                        show_preview=show_preview,
                        key=key,
                    )
                )
        if show_preview:
            for i, file_preview_container in enumerate(file_preview_infos):
                with file_preview_container:
                    download_and_display_file(files[i], default_height_if_needed=250)

    # MARK: LIST
    elif representation_mode == 2:
        file_preview_infos = []
        for file in files:
            file_preview_infos.append(line_file(file, show_preview=show_preview))
        if show_preview:
            for i, file_preview_container in enumerate(file_preview_infos):
                with file_preview_container:
                    download_and_display_file(files[i], default_height_if_needed=250)


def representation_mode_select():
    representation_options = ["🧮 Table", "🃏 Cards", "🏷️ List"]
    representation_mode = st.segmented_control(
        "Representation",
        options=range(len(representation_options)),
        format_func=lambda x: representation_options[x],
        default=1,
        key="representation",
    )
    if representation_mode is None:
        representation_mode = 1
    if representation_mode in [1, 2]:
        show_preview = st.toggle(
            "Show file preview",
            value=False,
            help="Toggle to show or hide file previews.",
        )
    if representation_mode == 1:
        nbr_of_files_per_line = st.slider(
            "Number of files per line",
            min_value=3,
            max_value=8,
            value=5,
            help="Adjust the number of files displayed per line.",
        )

    return (
        representation_mode,
        show_preview if representation_mode in [1, 2] else False,
        nbr_of_files_per_line if representation_mode == 1 else 3,
    )
