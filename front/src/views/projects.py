import requests
import streamlit as st
from core.files import display_files, representation_mode_select


def projects():
    projects = requests.get("http://back:80/projects").json()

    with st.sidebar:
        project = st.selectbox(
            "Select a project",
            options=projects,
            format_func=lambda x: x["name"],
            key="project_selector",
        )
        representation_mode, show_preview, nbr_of_files_per_line = (
            representation_mode_select()
        )


    files = requests.get(f"http://back:80/project/{project['name']}/files").json()
    # TODO
    calendar_records = []

    tabs = st.tabs(
        ["Project Details", "Project Files", "Project Calendar records"],
    )
    with tabs[0]:
        st.markdown(
            f"""
## <span style="color:{project['color']}; font-weight:bold;">{project['name']}</span>

- 🎨 **Color:** `{project['color']}`
- 📄 **Files:** `{len(files)}`
- 📆 **Calendar records:** `{len(calendar_records)}`

### 📝 Description:
""",
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            st.write(project["description"])

    with tabs[1]:
        display_files(
            files,
            representation_mode=representation_mode,
            show_preview=show_preview,
            nbr_of_files_per_line=nbr_of_files_per_line,
        )
    with tabs[2]:
        st.error("In dev...")


if __name__ == "__main__":
    projects()
