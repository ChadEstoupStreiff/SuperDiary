import requests
import streamlit as st
from core.files import display_files, representation_mode_select
from core.calendar import box_calendar_record

def projects():
    projects = requests.get("http://back:80/projects").json()

    with st.sidebar:
        project = st.selectbox(
            "Select a project",
            options=projects,
            format_func=lambda x: x["name"],
            key="project_selector",
        )
        with st.expander("File menu", expanded=False):
            representation_mode, show_preview, nbr_of_files_per_line = (
                representation_mode_select()
            )

    files = requests.get(f"http://back:80/project/{project['name']}/files")
    if files.status_code != 200:
        st.error("Project not found or no files available.")
        files = []
    else:
        files = files.json()

    records = requests.get(
        f"http://back:80/calendar/records?project={project['name']}"
    )
    if records.status_code != 200:
        st.error("Project not found or no calendar records available.")
        records = []
    else:
        records = records.json()

    tabs = st.tabs(
        ["Project Details", "Project Files", "Project Calendar records"],
    )
    with tabs[0]:
        st.markdown(
            f"""
## <span style="color:{project['color']}; font-weight:bold;">{project['name']}</span>

- 🎨 **Color:** `{project['color']}`
- 📄 **Files:** `{len(files)}`
- 📆 **Calendar records:** `{len(records)}`
- ⌛ **Time Spent:** `{sum(record['time_spent'] for record in records) if records else 0} hours`

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
        if records:
            cols = st.columns(5)
            for i, record in enumerate(records):
                with cols[i % 5]:
                    box_calendar_record(record, show_project=False)
        else:
            st.info("No calendar records found.")                


if __name__ == "__main__":
    projects()
