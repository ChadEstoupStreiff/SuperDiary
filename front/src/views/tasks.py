import pandas as pd
import requests
import streamlit as st


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


if __name__ == "__main__":
    st.set_page_config(
        page_title="Super Diary",
        page_icon="/assets/logo.png",
        layout="wide",
    )
    tasks()

if __name__ == "__main__":
    tasks()
