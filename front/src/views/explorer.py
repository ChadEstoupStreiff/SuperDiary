import streamlit as st
from core.explorer import search_engine
from core.files import display_files, representation_mode_select
from utils import get_setting


def generate_query_description(search_result):
    query_str = f"Found {len(search_result['files'])} files in {search_result['time_spent'].total_seconds():.3f}s with mode {search_result['search_mode']} beetween {search_result['start_date']} and {search_result['end_date']}"
    if search_result["query"] is not None and len(search_result["query"]) > 0:
        query_str += f" with query '{search_result['query']}'"
    if search_result["types"] is not None and len(search_result["types"]) > 0:
        query_str += (
            f" and types {', '.join(search_result['types'])}"
            + ("" if not search_result["exclude_file_types"] else " (excluded)")
        )
    if (
        search_result["subfolder"] is not None
        and len(search_result["subfolder"]) > 0
    ):
        query_str += (
            f" and subfolders {', '.join(search_result['subfolder'])}"
            + ("" if not search_result["exclude_subfolders"] else " (excluded)")
        )
    if (
        search_result["projects"] is not None
        and len(search_result["projects"]) > 0
    ):
        query_str += (
            f" and projects {', '.join(search_result['projects'])}"
            + ("" if not search_result["exclude_projects"] else " (excluded)")
        )
    if search_result["tags"] is not None and len(search_result["tags"]) > 0:
        query_str += (
            f" and tags {', '.join(search_result['tags'])}"
            + ("" if not search_result["exclude_tags"] else " (excluded)")
        )
    return query_str

def explorer():
    # MARK: SEARCH FORM
    search_result = search_engine()
    if search_result is not None:
        st.session_state.explorer_files = search_result

    with st.sidebar:
        representation_mode, show_preview, nbr_of_files_per_line = (
            representation_mode_select(
                default_mode=get_setting("explorer_default_representation_mode")
            )
        )

    if "explorer_files" in st.session_state:
        query_str = generate_query_description(st.session_state.explorer_files)
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
    else:
        st.info("Search for files first :)")


if __name__ == "__main__":
    explorer()
