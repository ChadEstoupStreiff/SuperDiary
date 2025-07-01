import pandas as pd
import requests
import streamlit as st
from utils import generate_tag_visual_markdown, toast_for_rerun


# MARK: Settings func
def load_settings():
    return requests.get("http://back:80/settings").json()


def apply_settings(settings):
    """
    Apply the settings selected by the user.
    This function is a placeholder for applying settings.
    """
    result = requests.post(
        "http://back:80/settings",
        json=settings,
    )
    if result.status_code == 200:
        st.toast("Settings applied successfully!", icon="✅")
    else:
        st.toast(
            "Failed to apply settings. Please try again later.",
            icon="❌",
        )


def ai_settings(prefix: str):
    pass


# MARK: Project func
@st.dialog("🆕 Create Project")
def dialog_create_project():
    """
    Dialog for creating a new project.
    """
    with st.form("create_project_form"):
        name = st.text_input(
            "Project Name",
            help="Enter the name of the project.",
            max_chars=50
        )
        description = st.text_area(
            "Project Description",
            help="Enter a brief description of the project.",
        )
        color = st.color_picker(
            "Project Color",
            value="#0000FF",  # Default to blue
            help="Select a color for the project.",
        )
        st.write(color)

        if st.form_submit_button("Create Project", use_container_width=True):
            response = requests.post(
                f"http://back:80/project?name={name}&description={description}&color={color[1:]}"
            )
            if response.status_code == 200:
                toast_for_rerun("Project created successfully!", icon="✅")
                st.rerun()
            else:
                st.error("Failed to create project. Please try again.")
                st.toast("Failed to create project. Please try again.", icon="❌")


@st.dialog("✏️ Edit Project")
def dialog_edit_project(project):
    """
    Dialog for editing an existing project.
    """
    with st.form("edit_project_form"):
        name = st.text_input(
            "Project Name",
            value=project["name"],
            help="Enter the name of the project.",
            max_chars=50,
        )
        description = st.text_area(
            "Project Description",
            value=project["description"] or "",
            help="Enter a brief description of the project.",
        )
        color = st.color_picker(
            "Project Color",
            value=project["color"],
            help="Select a color for the project.",
        )

        if st.form_submit_button("Update Project", use_container_width=True):
            response = requests.put(
                f"http://back:80/project/{project['name']}?name={name}&description={description}&color={color[1:]}",
            )
            if response.status_code == 200:
                toast_for_rerun("Project updated successfully!", icon="✅")
                st.rerun()
            else:
                st.error("Failed to update project. Please try again.")


@st.dialog("🗑️ Delete project")
def dialog_delete_project(project):
    st.markdown(
        f"### Deleting  <span style='color:{project['color']};'>{project['name']}</span>",
        unsafe_allow_html=True,
    )
    st.warning(
        "Beware this action is irreversible and will impact other module of the app such as calendar or explorer! Are you sure you want to delete this project?"
    )
    if st.button("Delete 🗑️", use_container_width=True):
        response = requests.delete(f"http://back:80/project/{project['name']}")
        if response.status_code == 200:
            toast_for_rerun("Project deleted successfully!", icon="🗑️")
            st.rerun()
        else:
            st.error("Failed to delete project. Please try again.")


# MARK: Tag func


@st.dialog("🆕 Create Tag")
def dialog_create_tag():
    """
    Dialog for creating a new tag.
    """
    with st.form("create_tag_form"):
        name = st.text_input(
            "Tag Name",
            help="Enter the name of the tag.",
            max_chars=20,
        )
        color = st.color_picker(
            "Tag Color",
            value="#FF0000",  # Default to red
            help="Select a color for the tag.",
        )

        if st.form_submit_button("Create Tag", use_container_width=True):
            response = requests.post(
                f"http://back:80/tag?name={name}&color={color[1:]}"
            )
            if response.status_code == 200:
                toast_for_rerun("Tag created successfully!", icon="✅")
                st.rerun()
            else:
                st.error("Failed to create tag. Please try again.")


@st.dialog("✏️ Edit Tag")
def dialog_edit_tag(tag):
    """
    Dialog for editing an existing tag.
    """
    with st.form("edit_tag_form"):
        name = st.text_input(
            "Tag Name",
            value=tag["name"],
            help="Enter the name of the tag.",
            max_chars=20,
        )
        color = st.color_picker(
            "Tag Color",
            value=tag["color"],
            help="Select a color for the tag.",
        )

        if st.form_submit_button("Update Tag", use_container_width=True):
            response = requests.put(
                f"http://back:80/tag/{tag['name']}?name={name}&color={color[1:]}"
            )
            if response.status_code == 200:
                toast_for_rerun("Tag updated successfully!", icon="✅")
                st.rerun()
            else:
                st.error("Failed to update tag. Please try again.")


@st.dialog("🗑️ Delete Tag")
def dialog_delete_tag(tag):
    st.markdown(
        f"### Deleting  <span style='color:{tag['color']};'>{tag['name']}</span>",
        unsafe_allow_html=True,
    )
    st.warning(
        "Beware this action is irreversible and will impact other module of the app such as calendar or explorer! Are you sure you want to delete this tag?"
    )
    if st.button("Delete 🗑️", use_container_width=True):
        response = requests.delete(f"http://back:80/tag/{tag['name']}")
        if response.status_code == 200:
            toast_for_rerun("Tag deleted successfully!", icon="🗑️")
            st.rerun()
        else:
            st.error("Failed to delete tag. Please try again.")


# MARK: Tasks func


def fetch_display_tasks(task_type: str, file: str = None):
    """
    Load tasks from the backend based on the task type and optional file.
    """
    result_health = requests.get(f"http://back:80/{task_type}/health")
    if result_health.status_code != 200:
        st.error(f"Failed to fetch {task_type} health status: {result_health.text}")
    else:
        health_status = result_health.json()
        result_running = requests.get(f"http://back:80/{task_type}/running")
        if result_running.status_code == 200 and result_running.json() is not None:
            st.caption(
                f"Daemon health: {health_status} - {result_running.content.decode('utf-8')}"
            )
        else:
            st.caption(f"Daemon health: {health_status}")

    result_tasks = requests.get(
        f"http://back:80/{task_type}/tasks" + (f"/{file}" if file else "")
    )
    if result_tasks.status_code == 200:
        tasks = result_tasks.json()
        if tasks:
            tasks_df = pd.DataFrame(tasks)
            st.dataframe(
                tasks_df, use_container_width=True, hide_index=True, height=300
            )
        else:
            st.warning(f"No {task_type} tasks available.")
    else:
        st.error(f"Failed to fetch {task_type} tasks: {result_tasks.text}")


def tasks(
    file=None,
    list_ocr: bool = True,
    list_transcription: bool = True,
):
    with st.expander("Summarization Tasks", expanded=True):
        fetch_display_tasks("summarize", file)

    if list_ocr:
        with st.expander("OCR Tasks", expanded=True):
            fetch_display_tasks("ocr", file)

    if list_transcription:
        with st.expander("Transcription Tasks", expanded=True):
            fetch_display_tasks("transcription", file)


def settings():
    """
    Settings page for the application.
    This function is a placeholder for the settings view.
    """
    settings_tabs = st.tabs(
        [
            "Application Settings",
            "Projects Management",
            "Tags Management",
            "LLM Settings",
            "Tasks",
        ]
    )

    result = requests.get("http://back:80/ollama/list")
    if result.status_code == 200:
        installed_models = [m["name"] for m in result.json()]
    else:
        installed_models = None

        if installed_models is None:
            st.error("Failed to fetch installed models. Please try again later.")

    with settings_tabs[0]:
        # MARK: Application Settings
        with st.form("settings_form"):
            settings = load_settings()

            top = st.container()

            with st.expander("Summarization Settings", expanded=True):
                settings["enable_auto_summary"] = st.toggle(
                    "Enable auto Summarization",
                    value=settings["enable_auto_summary"],
                    help="Enable automatic summarization of text files when uploaded.",
                )
                settings["summarization_model"] = st.selectbox(
                    "Summarization model",
                    options=installed_models if installed_models else [],
                    index=installed_models.index(settings["summarization_model"]),
                    help="Select the model to use for summarization.",
                )

            with st.expander("OCR Settings", expanded=True):
                st.caption(
                    "Note: The OCR feature is only available for image files (e.g., png, jpg, jpeg, bmp, webp)."
                )
                settings["enable_auto_ocr"] = st.toggle(
                    "Enable auto OCR Processing",
                    value=settings["enable_auto_ocr"],
                    help="Enable automatic OCR processing of image files when uploaded.",
                )

            with st.expander("Transcription Settings", expanded=True):
                st.caption(
                    "Note: The transcription feature is only available for audio files (e.g., mp3, wav, mp4, mov, avi)."
                )
                settings["enable_auto_transcription"] = st.toggle(
                    "Enable auto Transcription",
                    value=settings["enable_auto_transcription"],
                    help="Enable automatic transcription of audio files when uploaded.",
                )
                transcription_models = ["tiny", "base", "small", "medium", "large-v3"]
                settings["transcription_model"] = st.radio(
                    "Transcription model",
                    options=transcription_models,
                    index=transcription_models.index(settings["transcription_model"]),
                    horizontal=True,
                )
                st.caption(
                    "Note: The higher the model, the more accurate the transcription, but it requires more resources, make sure you have enough RAM."
                )
                st.markdown("""
| Model       | Speed     | RAM Needed        | WER (English) |
|-------------|-----------|-------------------|---------------|
| tiny        | Fastest   | ~1–2 GB           | ~14–15%       |
| base        | Very fast | ~2–3 GB           | ~10–11%       |
| small       | Fast      | ~4–5 GB           | ~6–7%         |
| medium      | Slower    | ~7–8 GB           | ~4–5%         |
| large-v3    | Slowest   | ~10–12 GB         | ~2.7%         |
""")

            with top:
                if st.form_submit_button("Apply Settings", use_container_width=True):
                    apply_settings(settings)
            if st.form_submit_button("Apply settings", use_container_width=True):
                apply_settings(settings)

    # MARK: Projects Management
    with settings_tabs[1]:
        if st.button("🆕 Create new project", use_container_width=True):
            dialog_create_project()

        projects = requests.get("http://back:80/projects").json()
        if len(projects) == 0:
            st.warning(
                "No projects available. Please create a new project. Default ones will be created at next app restart."
            )
        for project in projects:
            with st.container(border=True, key=f"project_{project['name']}"):
                cols = st.columns([5, 1])
                with cols[0]:
                    st.markdown(
                        f"### <span style='color:{project['color']};'>{project['name']}</span>",
                        unsafe_allow_html=True,
                    )
                    st.caption(project["description"] or "No description provided.")
                with cols[1]:
                    if st.button(
                        "✏️",
                        key=f"edit_project_{project['name']}",
                        use_container_width=True,
                        help="✏️ Edit",
                    ):
                        dialog_edit_project(project)
                    if st.button(
                        "🗑️",
                        key=f"delete_project_{project['name']}",
                        use_container_width=True,
                        help="🗑️ Delete",
                    ):
                        dialog_delete_project(project)

    # MARK: Tags Management
    with settings_tabs[2]:
        if st.button("🆕 Create new tag", use_container_width=True):
            dialog_create_tag()

        tags = requests.get("http://back:80/tags").json()
        if len(tags) == 0:
            st.warning(
                "No tags available. Please create a new tag. Default ones will be created at next app restart."
            )
        for tag in tags:
            with st.container(border=True, key=f"tag_{tag['name']}"):
                cols = st.columns([5, 1])
                with cols[0]:
                    st.markdown(
                        generate_tag_visual_markdown(tag["name"], tag["color"]),
                        unsafe_allow_html=True,
                    )
                with cols[1]:
                    if st.button(
                        "✏️",
                        key=f"edit_tag_{tag['name']}",
                        use_container_width=True,
                        help="✏️ Edit",
                    ):
                        dialog_edit_tag(tag)
                    if st.button(
                        "🗑️",
                        key=f"delete_tag_{tag['name']}",
                        use_container_width=True,
                        help="🗑️ Delete",
                    ):
                        dialog_delete_tag(tag)

    # MARK: LLM Settings
    with settings_tabs[3]:
        tab_llama, tab_chatgpt, tab_gemini = st.tabs(
            ["Local Llama", "OpenAI ChatGPT", "Google Gemini"]
        )

        with st.expander("LLM Settings", expanded=True):
            with tab_llama:
                cols = st.columns(2)
                with cols[0]:
                    model_pull_name = st.text_input(
                        "Model to install",
                        help="Enter the name of the model to pull from Ollama.",
                    )
                    st.caption(
                        "See available models at this link: https://ollama.com/library"
                    )
                    if st.button("Pull Model", use_container_width=True):
                        with st.spinner("Pulling model..."):
                            if model_pull_name:
                                result = requests.post(
                                    f"http://back:80/ollama/pull/{model_pull_name}"
                                )
                                if result.status_code == 200:
                                    st.toast(
                                        f"Model '{model_pull_name}' pulled successfully.",
                                        icon="✅",
                                    )
                                    installed_models = requests.get(
                                        "http://back:80/ollama/list"
                                    ).json()
                                else:
                                    st.toast(
                                        f"Failed to pull model '{model_pull_name}'. Please try again.",
                                        icon="❌",
                                    )
                            else:
                                st.warning("Please enter a model name to pull.")
                with cols[1]:
                    st.subheader("Installed Models:")
                    for model in installed_models:
                        st.badge(model)
            with tab_chatgpt:
                st.error("In dev...")
            with tab_gemini:
                st.error("In dev...")

    # MARK: Tasks
    with settings_tabs[4]:
        tasks(
            file=None,
            list_ocr=True,
            list_transcription=True,
        )


if __name__ == "__main__":
    settings()
