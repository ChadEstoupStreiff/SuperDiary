import json

import requests
import streamlit as st
from core.calendar import box_calendar_record
from core.files import display_files, representation_mode_select
from utils import toast_for_rerun


def change_project():
    del st.session_state["project_notes"]


def update_todo(project_name, todo):
    for item in todo:
        if item["Done"] is None:
            item["Done"] = False
        if item["Task"] is None:
            item["Task"] = ""
    todo.sort(key=lambda x: x["Done"])
    response = requests.post(
        f"http://back:80/project/{project_name}/todo?todo={json.dumps(todo)}",
    )
    if response.status_code == 200:
        toast_for_rerun(
            "TODO list updated successfully!",
            icon="✅",
        )
        st.rerun()
    else:
        st.error(f"Error updating TODO list: {response.text}")
        st.toast(
            f"Error updating TODO list: {response.text}",
            icon="❌",
        )


def projects():
    projects = requests.get("http://back:80/projects").json()

    with st.sidebar:
        project = st.selectbox(
            "Select a project",
            options=projects,
            format_func=lambda x: x["name"],
            on_change=change_project,
            key="project_selector",
        )

    files = requests.get(f"http://back:80/project/{project['name']}/files")
    if files.status_code != 200:
        st.error("Project not found or no files available.")
        files = []
    else:
        files = files.json()

    records = requests.get(f"http://back:80/calendar/search?project={project['name']}")
    if records.status_code != 200:
        st.error("Project not found or no calendar records available.")
        records = []
    else:
        records = records.json()

    tabs = st.tabs(
        ["📋 Details", "📁 Files", "📅 Calendar", "📝 Notes", "✅ TODO"],
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
        with st.columns([1, 4])[0]:
            representation_mode, show_preview, nbr_of_files_per_line = (
                representation_mode_select()
            )
        st.divider()
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
    with tabs[3]:
        notes = requests.get(f"http://back:80/project/{project['name']}/notes").json()
        top = st.container()
        edited_notes = st.text_area(
            "Project Notes",
            value=notes,
            height=1000,
            key="project_notes",
            label_visibility="hidden",
        )

        with top:
            if st.button(
                "📝 Save Notes",
                help="Click to save the project notes.",
                use_container_width=True,
            ):
                if edited_notes != notes:
                    response = requests.post(
                        f"http://back:80/project/{project['name']}/notes?notes={edited_notes}"
                    )
                    if response.status_code == 200:
                        toast_for_rerun(
                            "Project notes updated successfully.",
                            icon="✅",
                        )
                        st.rerun()
                    else:
                        st.toast(
                            "Failed to update project notes.",
                            icon="❌",
                        )

    with tabs[4]:
        todo = requests.get(f"http://back:80/project/{project['name']}/todo")
        if todo.status_code == 200:
            todo = todo.json()
            if not todo:
                todo = [{"Done": False, "Task": ""}]

            new_todo = st.data_editor(
                todo,
                column_config={
                    "Done": st.column_config.CheckboxColumn("Done", width=None),
                    "Task": st.column_config.TextColumn("Task", width="large"),
                },
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                key="project_todo_table",
            )

            if new_todo != todo:
                update_todo(project["name"], new_todo)
                toast_for_rerun(
                    "TODO list updated successfully.",
                    icon="✅",
                )
                st.rerun()
        else:
            st.error("Failed to fetch TODO items.")


if __name__ == "__main__":
    projects()
