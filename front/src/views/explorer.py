import datetime

import streamlit as st
from core.explorer import search_engine, search_files
from core.files import display_files, representation_mode_select


def explorer():
    # MARK: SEARCH FORM
    search_result = search_engine()
    if search_result is not None:
        st.session_state.explorer_files = search_result

    with st.sidebar:
        representation_mode, show_preview, nbr_of_files_per_line = (
            representation_mode_select()
        )

    if "explorer_files" not in st.session_state:
        search_result = search_files(
            None,
            datetime.date.today() - datetime.timedelta(days=7),
            datetime.date.today(),
        )
        if search_result is not None:
            st.session_state.explorer_files = search_result

    if "explorer_files" in st.session_state:
        time_spent = st.session_state.explorer_files.get(
            "time_spent", -1
        ).total_seconds()
        query_str = f"Found {len(st.session_state.explorer_files['files'])} files in {time_spent:.3f}s beetween {st.session_state.explorer_files['start_date']} and {st.session_state.explorer_files['end_date']}"
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
            query_str += (
                f" and tags {', '.join(st.session_state.explorer_files['tags'])}"
            )
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
