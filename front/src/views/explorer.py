import datetime
from typing import List

import requests
import streamlit as st
from core.files import display_files, representation_mode_select
from utils import mimes, mimes_map


def search_files(
    text: str,
    start_date: datetime,
    end_date: datetime,
    subfolder: List[str],
    types: List[str],
    projects: List[str],
    tags: List[str],
):
    # TODO : Add support for projects filtering
    # MARK: SEARCH FILES
    with st.spinner("Searching files..."):
        request = (
            f"http://back:80/files/search?start_date={start_date}&end_date={end_date}"
        )
        if text is not None:
            request += f"&text={text}"
        if subfolder is not None and len(subfolder) > 0:
            request += f"&subfolder={','.join(subfolder)}"
        if types is not None and len(types) > 0:
            request += f"&types={','.join(types)}"
        if projects is not None and len(projects) > 0:
            request += f"&projects={','.join(projects)}"
        if tags is not None and len(tags) > 0:
            request += f"&tags={','.join(tags)}"

        result = requests.get(request)
    if result.status_code == 200:
        st.toast(
            f"Found {len(result.json())} files matching the criteria.",
        )
        st.session_state.explorer_files = {
            "query": text,
            "start_date": start_date,
            "end_date": end_date,
            "types": types,
            "subfolder": subfolder,
            "projects": projects,
            "tags": tags,
            "files": result.json(),
        }
    else:
        st.toast(
            f"Failed to search files: {result.text}",
            icon="❌",
        )
        st.error(f"Failed to search files: {result.text}")
        st.session_state.explorer_files = {
            "query": text,
            "start_date": start_date,
            "end_date": end_date,
            "types": types,
            "subfolder": subfolder,
            "projects": projects,
            "tags": tags,
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
        with cols[2]:
            subfolder = st.multiselect(
                "Subfolders",
                options=[
                    "uploads",
                    "notes",
                    "audio",
                ],
                key="subfolders",
                help="Select subfolders to filter files.",
            )

        with cols[3]:
            projects_list = requests.get("http://back:80/projects").json()
            projects = st.multiselect(
                "Projects",
                options=[p["name"] for p in projects_list],
                key="projects",
                help="Select projects to filter files.",
            )

        with cols[4]:
            tags_list = requests.get("http://back:80/tags").json()
            tags = st.multiselect(
                "Tags",
                options=[t["name"] for t in tags_list],
                key="tags",
                help="Select tags to filter files.",
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
                subfolder,
                file_types,
                projects,
                tags,
            )

    with st.sidebar:
        representation_mode, show_preview, nbr_of_files_per_line = (
            representation_mode_select()
        )

    if "explorer_files" not in st.session_state:
        search_files(
            None,
            datetime.date.today() - datetime.timedelta(days=7),
            datetime.date.today(),
            [],
            [],
            [],
            [],
        )
    if "explorer_files" in st.session_state:
        query_str = f"Found {len(st.session_state.explorer_files['files'])} files beetween {st.session_state.explorer_files['start_date']} and {st.session_state.explorer_files['end_date']}"
        if (
            st.session_state.explorer_files["query"] is not None
            and len(st.session_state.explorer_files["query"]) > 0
        ):
            query_str += f" with query '{st.session_state.explorer_files['query']}'"
        if (
            st.session_state.explorer_files["types"] is not None
            and len(st.session_state.explorer_files["types"]) > 0
        ):
            query_str += (
                f" and types {', '.join(st.session_state.explorer_files['types'])}"
            )
        if (
            st.session_state.explorer_files["subfolder"] is not None
            and len(st.session_state.explorer_files["subfolder"]) > 0
        ):
            query_str += f" and subfolders {', '.join(st.session_state.explorer_files['subfolder'])}"
        if (
            st.session_state.explorer_files["projects"] is not None
            and len(st.session_state.explorer_files["projects"]) > 0
        ):
            query_str += f" and projects {', '.join(st.session_state.explorer_files['projects'])}"
        if (
            st.session_state.explorer_files["tags"] is not None
            and len(st.session_state.explorer_files["tags"]) > 0
        ):
            query_str += f" and tags {', '.join(st.session_state.explorer_files['tags'])}"
        st.caption(query_str)

        if len(st.session_state.explorer_files["files"]) > 0:
            # MARK: TABLE
            display_files(
                st.session_state.explorer_files["files"],
                representation_mode=representation_mode,
                nbr_of_files_per_line=nbr_of_files_per_line,
                show_preview=show_preview,
            )
        else:
            st.write("No files found in the system.")


if __name__ == "__main__":
    explorer()
