import datetime
import os
from typing import List

import pandas as pd
import requests
import streamlit as st
from pages import PAGE_VIEWER
from utils import download_and_display_file, mimes, mimes_map


def box_file(file: str, height: int, show_preview: bool):
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
        st.markdown(f"#### {file_name}")
        st.caption(f"**Date:** {date}")
        st.caption(f"**Subfolder:** {subfolder}")
        st.caption(f"**Path:** {file}")

        with cols[0]:
            if st.button(
                "🔎",
                help="Click to view file details.",
                use_container_width=True,
                key=f"view_{file}",
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
                key=f"download_{file}",
            )
    return preview


def line_file(file: str, show_preview: bool):
    MAX_SUMMARY_LENGTH = 500

    # MARK: LINE FILE
    with st.container(border=True):
        file_name = os.path.basename(file)
        date = file.split("/")[2]
        subfolder = file.split("/")[3]

        cols = st.columns([2, 2, 3, 1] if show_preview else [2, 3, 1])
        with cols[1 if show_preview else 0]:
            st.markdown(f"#### {file_name}")
            st.caption(f"**Date:** {date}")
            st.caption(f"**Subfolder:** {subfolder}")
            st.caption(f"**Path:** {file}")
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
                key=f"view_{file}",
            ):
                st.session_state.file_to_see = file
                st.switch_page(PAGE_VIEWER)
            st.download_button(
                "📥",
                f"http://back:80/files/download/{file}",
                file_name=file_name,
                help="Click to download the file.",
                use_container_width=True,
                key=f"download_{file}",
            )
        if show_preview:
            return cols[0].container(
                border=True,
                height=300,
            )
        return None


def search_files(text: str, start_date: datetime, end_date: datetime, types: List[str]):
    # MARK: SEARCH FILES
    with st.spinner("Searching files..."):
        request = (
            f"http://back:80/files/search?start_date={start_date}&end_date={end_date}"
        )
        if text is not None:
            request += f"&text={text}"
        if types is not None and len(types) > 0:
            request += f"&types={','.join(types)}"

        result = requests.get(request)
    if result.status_code == 200:
        st.session_state.explorer_files = {
            "query": text,
            "start_date": start_date,
            "end_date": end_date,
            "types": types,
            "files": result.json(),
        }
    else:
        st.error(f"Failed to search files: {result.text}")
        st.session_state.explorer_files = {
            "query": text,
            "start_date": start_date,
            "end_date": end_date,
            "types": types,
            "files": [],
        }


def explorer():
    # MARK: SEARCH FORM
    with st.form("file_search_form", clear_on_submit=False):
        search_text = st.text_input(
            "Search files",
            placeholder="Enter file name, content or keyword...",
            key="search_files",
        )
        cols = st.columns(5)
        with cols[0]:
            search_dates = st.date_input(
                "Search by date",
                value=(
                    datetime.date.today() - datetime.timedelta(days=7),
                    datetime.date.today(),
                ),
                key="search_dates",
                help="Select a date to filter files.",
            )
        with cols[1]:
            file_types = st.multiselect(
                "File Types",
                options=mimes,
                format_func=lambda x: mimes_map[x],
                key="file_types",
                help="Select file types to filter files.",
            )

        if st.form_submit_button(
            "Search",
            use_container_width=True,
            help="Click to search files based on the criteria.",
        ):
            search_files(
                search_text if len(search_text) > 0 else None,
                search_dates[0],
                search_dates[1],
                file_types,
            )

    with st.sidebar:
        representation_options = ["🧮 Table", "🃏 Cards", "🏷️ List"]
        representation_mode = st.segmented_control(
            "Representation",
            options=range(len(representation_options)),
            format_func=lambda x: representation_options[x],
            default=1,
            key="representation",
        )
        nbr_of_files_per_line = st.slider(
            "Number of files per line",
            min_value=3,
            max_value=10,
            value=5,
            help="Adjust the number of files displayed per line.",
        )
        if representation_mode == 1 or representation_mode == 2:
            show_preview = st.checkbox(
                "Show file preview",
                value=False,
                help="Toggle to show or hide file previews.",
            )

    if "explorer_files" not in st.session_state:
        search_files(
            None,
            datetime.date.today() - datetime.timedelta(days=7),
            datetime.date.today(),
            [],
        )
    if "explorer_files" in st.session_state:
        query_str = f"Found {len(st.session_state.explorer_files['files'])} files beetween {st.session_state.explorer_files['start_date']} and {st.session_state.explorer_files['end_date']}"
        if st.session_state.explorer_files["query"] is not None:
            query_str += f" with query '{st.session_state.explorer_files['query']}'"
        if st.session_state.explorer_files["types"] is not None:
            query_str += (
                f" and types {', '.join(st.session_state.explorer_files['types'])}"
            )
        st.caption(query_str)
        
        if len(st.session_state.explorer_files["files"]) > 0:
            files = st.session_state.explorer_files["files"]
            # MARK: TABLE
            if representation_mode == 0:
                table = pd.DataFrame(
                    [
                        {
                            "File": os.path.basename(file),
                            "Date": file.split("/")[2],
                            "Subfolder": file.split("/")[3],
                            "Path": file,
                        }
                        for file in files
                    ]
                )
                st.dataframe(
                    table,
                    use_container_width=True,
                    hide_index=True,
                    key="lines",
                )

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
                            )
                        )
                if show_preview:
                    for i, file_preview_container in enumerate(file_preview_infos):
                        with file_preview_container:
                            download_and_display_file(
                                files[i], default_height_if_needed=250
                            )

            # MARK: LIST
            elif representation_mode == 2:
                file_preview_infos = []
                for file in files:
                    file_preview_infos.append(
                        line_file(file, show_preview=show_preview)
                    )
                if show_preview:
                    for i, file_preview_container in enumerate(file_preview_infos):
                        with file_preview_container:
                            download_and_display_file(
                                files[i], default_height_if_needed=250
                            )
        else:
            st.write("No files found in the system.")


if __name__ == "__main__":
    explorer()
