import pandas as pd
import requests
import streamlit as st


def tasks(
    file=None,
    print_errors: bool = True,
    list_ocr: bool = True,
    list_transcription: bool = True,
):
    with st.expander("Summarization Tasks", expanded=True):
        response = requests.get(
            "http://back:80/summarization/tasks" + (f"/{file}" if file else "")
        )
        if response.status_code == 200:
            tasks = response.json()
            tasks_df = pd.DataFrame(tasks)
            st.dataframe(
                tasks_df, use_container_width=True, hide_index=True, height=500
            )
        else:
            if print_errors:
                st.error(f"Failed to fetch summarization tasks: {response.text}")
            else:
                st.warning("No summarization tasks available or failed to fetch tasks.")

    if list_ocr:
        with st.expander("OCR Tasks", expanded=True):
            response = requests.get(
                "http://back:80/ocr/tasks" + (f"/{file}" if file else "")
            )
            if response.status_code == 200:
                tasks = response.json()
                tasks_df = pd.DataFrame(tasks)
                st.dataframe(
                    tasks_df, use_container_width=True, hide_index=True, height=500
                )
            else:
                if print_errors:
                    st.error(f"Failed to fetch OCR tasks: {response.text}")
                else:
                    st.warning("No OCR tasks available or failed to fetch tasks.")

    if list_transcription:
        with st.expander("Transcription Tasks", expanded=True):
            response = requests.get(
                "http://back:80/transcription/tasks" + (f"/{file}" if file else "")
            )
            if response.status_code == 200:
                tasks = response.json()
                tasks_df = pd.DataFrame(tasks)
                st.dataframe(
                    tasks_df, use_container_width=True, hide_index=True, height=500
                )
            else:
                if print_errors:
                    st.error(f"Failed to fetch transcription tasks: {response.text}")
                else:
                    st.warning(
                        "No transcription tasks available or failed to fetch tasks."
                    )
