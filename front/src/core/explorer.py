import datetime
from typing import List

import requests
import streamlit as st
from utils import mimes, mimes_map


def search_files(
    text: str,
    start_date: datetime,
    end_date: datetime,
    subfolder: List[str] = None,
    types: List[str] = None,
    projects: List[str] = None,
    tags: List[str] = None,
    search_mode: int = 0,
    exclude_file_types: bool = False,
    exclude_subfolders: bool = False,
    exclude_projects: bool = False,
    exclude_tags: bool = False,
):
    # MARK: SEARCH FILES
    with st.spinner("Searching files...", show_time=True):
        request = f"http://back:80/files/search?start_date={start_date}&end_date={end_date}&search_mode={search_mode}"
        if text is not None:
            request += f"&text={text}"
        if subfolder is not None and len(subfolder) > 0:
            request += f"&subfolder={','.join(subfolder)}&exclude_subfolders={exclude_subfolders}"
        if types is not None and len(types) > 0:
            request += (
                f"&types={','.join(types)}&exclude_file_types={exclude_file_types}"
            )
        if projects is not None and len(projects) > 0:
            request += (
                f"&projects={','.join(projects)}&exclude_projects={exclude_projects}"
            )
        if tags is not None and len(tags) > 0:
            request += f"&tags={','.join(tags)}&exclude_tags={exclude_tags}"

        start_time = datetime.datetime.now()
        result = requests.get(request)
        end_time = datetime.datetime.now()

    files = []
    if result.status_code == 200:
        st.toast(
            f"Found {len(result.json())} files matching the criteria.",
        )
        files = result.json()
    else:
        st.toast(
            f"Failed to search files: {result.text}",
            icon="❌",
        )
        st.error(f"Failed to search files: {result.text}")
    return {
        "query": text,
        "start_date": start_date,
        "end_date": end_date,
        "types": types,
        "subfolder": subfolder,
        "projects": projects,
        "tags": tags,
        "files": files,
        "search_mode": search_mode,
        "time_spent": end_time - start_time,
        "exclude_file_types": exclude_file_types,
        "exclude_subfolders": exclude_subfolders,
        "exclude_projects": exclude_projects,
        "exclude_tags": exclude_tags,
    }


def search_engine(nbr_columns: int = 6):
    with st.form("file_search_form", clear_on_submit=False):
        search_text = st.text_input(
            "Search files",
            placeholder="Enter file name, content or keyword...",
            key="search_files",
        )
        cols = st.columns(nbr_columns)
        with cols[0]:
            with st.container(height=120, border=False):
                search_dates = st.date_input(
                    "Search by date",
                    value=(
                        datetime.date.today() - datetime.timedelta(days=7),
                        datetime.date.today(),
                    ),
                    key="search_dates",
                    help="Select a date to filter files.",
                )
        with cols[1 % nbr_columns]:
            with st.container(height=120, border=False):
                file_types = st.multiselect(
                    "File Types",
                    options=mimes,
                    format_func=lambda x: mimes_map[x],
                    key="file_types",
                    help="Select file types to filter files.",
                )
                exclude_file_types = st.toggle(
                    "Exclude File Types",
                    key="exclude_file_types",
                    help="Toggle to exclude selected file types from the search.",
                )
        with cols[2 % nbr_columns]:
            with st.container(height=120, border=False):
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
                exuclude_subfolders = st.toggle(
                    "Exclude Subfolders",
                    key="exclude_subfolders",
                    help="Toggle to exclude selected subfolders from the search.",
                )

        with cols[3 % nbr_columns]:
            with st.container(height=120, border=False):
                projects_list = requests.get("http://back:80/projects").json()
                projects = st.multiselect(
                    "Projects",
                    options=[p["name"] for p in projects_list],
                    key="projects",
                    help="Select projects to filter files.",
                )
                exclude_projects = st.toggle(
                    "Exclude Projects",
                    key="exclude_projects",
                    help="Toggle to exclude selected projects from the search.",
                )

        with cols[4 % nbr_columns]:
            with st.container(height=120, border=False):
                tags_list = requests.get("http://back:80/tags").json()
                tags = st.multiselect(
                    "Tags",
                    options=[t["name"] for t in tags_list],
                    key="tags",
                    help="Select tags to filter files.",
                )
                exclude_tags = st.toggle(
                    "Exclude Tags",
                    key="exclude_tags",
                    help="Toggle to exclude selected tags from the search.",
                )

        with cols[5 % nbr_columns]:
            with st.container(height=120, border=False):
                representation_options = [
                    "⚡️",
                    "🔍",
                    "🧠",
                ]
                search_mode = st.segmented_control(
                    "Search mode",
                    options=range(len(representation_options)),
                    format_func=lambda x: representation_options[x],
                    default=1,
                    help="Choose the search mode (⚡️ Quick, 🔍 Normal, 🧠 Deep). Quick Search is fast but less accurate — it only looks at keywords and notes. Normal Search also includes summaries. Deep Search is the most thorough (and slowest), scanning the full file content.",
                    key="search_mode",
                )
                if search_mode is None:
                    search_mode = 1

        if st.form_submit_button(
            "Search",
            use_container_width=True,
            help="Click to search files based on the criteria.",
        ):
            return search_files(
                search_text if len(search_text) > 0 else None,
                search_dates[0],
                search_dates[1],
                subfolder,
                file_types,
                projects,
                tags,
                search_mode,
                exclude_file_types=exclude_file_types,
                exclude_subfolders=exuclude_subfolders,
                exclude_projects=exclude_projects,
                exclude_tags=exclude_tags,
            )
    return None
