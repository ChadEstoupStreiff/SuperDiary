import json

import requests
import streamlit as st
from core.calendar import box_calendar_record
from core.files import display_files, representation_mode_select
from utils import get_setting, refractor_text_area, toast_for_rerun


def change_project():
    # del st.session_state["project_notes"]
    # del st.session_state["project_todo_table"]
    pass


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
""",
            unsafe_allow_html=True,
        )
        if project["description"]:
            st.markdown("### 📝 Description:")
            with st.container(border=True):
                st.write(project["description"])

    with tabs[1]:
        with st.columns([1, 4])[0]:
            representation_mode, show_preview, nbr_of_files_per_line = (
                representation_mode_select(
                    default_mode=get_setting("projects_default_representation_mode")
                )
            )
        st.divider()
        display_files(
            files,
            representation_mode=representation_mode,
            show_preview=show_preview,
            nbr_of_files_per_line=nbr_of_files_per_line,
            allow_multiple_selection=True,
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
        response = requests.get(f"http://back:80/project/{project['name']}/notes")
        if response.status_code != 200:
            st.error("Failed to load project notes.")
        else:
            notes = response.json()

            def update_notes(notes):
                if "project_notes" in st.session_state:
                    edited_notes = st.session_state["project_notes"]
                    response = requests.post(
                        f"http://back:80/project/{project['name']}/notes?notes={edited_notes}"
                    )
                    if response.status_code != 200:
                        toast_for_rerun(
                            "Failed to update project notes.",
                            icon="❌",
                        )
                    else:
                        toast_for_rerun(
                            "Project notes updated successfully.",
                            icon="✅",
                        )

            refractor_text_area(
                "Project Notes",
                value=notes,
                height=1000,
                on_change=update_notes,
                key="project_notes",
                label_visibility="hidden",
                args=(notes,),
            )
    with tabs[4]:
        response = requests.get(f"http://back:80/project/{project['name']}/todo")
        if response.status_code != 200:
            st.error("Failed to load TODO list.")
        else:
            todo_table = response.json()

            def update_todo(todo_table):
                if "project_todo_table" in st.session_state:
                    todo_editions = st.session_state["project_todo_table"][
                        "edited_rows"
                    ]
                    todo_deletions = st.session_state["project_todo_table"][
                        "deleted_rows"
                    ]
                    todo_additions = st.session_state["project_todo_table"][
                        "added_rows"
                    ]

                    if len(todo_deletions) > 0:
                        todo_table = [
                            todo_table[i]
                            for i in range(len(todo_table))
                            if i not in todo_deletions
                        ]
                    for index, editions in todo_editions.items():
                        for key, value in editions.items():
                            todo_table[index][key] = value
                    for _ in todo_additions:
                        todo_table.append({"Done": False, "Task": ""})

                    todo_table.sort(key=lambda x: x["Done"])

                    response = requests.post(
                        f"http://back:80/project/{project['name']}/todo?todo={json.dumps(todo_table)}",
                    )
                    if response.status_code != 200:
                        st.error(f"Error updating TODO list: {response.text}")
                        st.toast(
                            f"Error updating TODO list: {response.text}",
                            icon="❌",
                        )

            st.data_editor(
                todo_table,
                column_config={
                    "Done": st.column_config.CheckboxColumn("Done", width=None),
                    "Task": st.column_config.TextColumn("Task", width="large"),
                },
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                key="project_todo_table",
                on_change=update_todo,
                args=(todo_table,),
            )


if __name__ == "__main__":
    projects()
