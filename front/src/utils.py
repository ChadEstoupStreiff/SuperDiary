import base64
import json
import mimetypes
import os
import tempfile

import pandas as pd
import requests
import streamlit as st

map_languauge_extension = {
    "py:": "python",
    "js:": "javascript",
    "ts:": "typescript",
    "java:": "java",
    "c:": "c",
    "cpp:": "cpp",
    "csharp:": "csharp",
    "html:": "html",
    "css:": "css",
    "yaml:": "yaml",
    "bash:": "bash",
    "sh:": "bash",
    "sql:": "sql",
    "php:": "php",
    "ruby:": "ruby",
    "go:": "go",
    "rust:": "rust",
    "kotlin:": "kotlin",
    "swift:": "swift",
}


def display_file(file_path: str, file_url: str, default_height_if_needed: int = 1000):
    file_url = file_url.replace("http://back:80", "http://localhost:8400")
    file_extension = file_path.split(".")[-1].lower()

    if not os.path.exists(file_path):
        st.error(f"File {file_path} does not exist.")
        return

    try:
        if (
            file_extension == "xlsx"
            or file_extension == "xls"
            or file_extension == "ods"
            or file_extension == "xlsm"
            or file_extension == "csv"
        ):
            st.dataframe(
                pd.read_csv(file_path),
                use_container_width=True,
                height=1000,
                key=f"dataframe_{file_path}",
            )

        else:
            with open(file_path, "rb") as file:
                file_bytes = file.read()

                if (
                    file_extension == "png"
                    or file_extension == "jpg"
                    or file_extension == "jpeg"
                    or file_extension == "bmp"
                    or file_extension == "webp"
                    or file_extension == "gif"
                ):
                    st.image(file_bytes, use_container_width=True)

                elif file_extension == "txt":
                    st.code(
                        file_bytes.decode("utf-8"),
                    )

                elif file_extension == "json":
                    st.json(json.loads(file_bytes.decode("utf-8")))

                elif file_extension == "mp3" or file_extension == "wav":
                    st.audio(file_bytes, format="audio/wav")

                elif (
                    file_extension == "mp4"
                    or file_extension == "avi"
                    or file_extension == "mov"
                ):
                    st.video(file_bytes, format="video/mp4")

                elif file_extension == "md" or file_extension == "markdown":
                    st.markdown(file_bytes.decode("utf-8"), unsafe_allow_html=True)

                elif file_extension in map_languauge_extension:
                    language = map_languauge_extension[file_extension]
                    st.code(
                        file_bytes.decode("utf-8"),
                        language=language,
                    )

                elif file_extension == "pdf":
                    media_type, _ = mimetypes.guess_type(file_path)
                    if not media_type:
                        media_type = "application/octet-stream"
                    encoded_content_string = base64.b64encode(file_bytes).decode(
                        "utf-8"
                    )
                    data_uri = f"data:{media_type};base64,{encoded_content_string}"
                    st.markdown(
                        f'<embed src="{data_uri}" width="100%" height="{default_height_if_needed}px" />',
                        unsafe_allow_html=True,
                    )

                else:
                    st.error(
                        f"Can't load a preview for this file type. {file_extension} is not supported."
                    )
    except Exception as e:
        st.error(
            f"File might be corrupted or not supported. Error displaying file: {str(e)}"
        )


def download_and_display_file(file_name, default_height_if_needed=1000):
    file_url = f"http://back:80/files/download/{file_name}"
    with st.spinner("Downloading file..."):
        result = requests.get(file_url)
    if result.status_code == 200:
        file_extension = os.path.splitext(file_name)[1].lower()
        with tempfile.NamedTemporaryFile(
            delete=True, suffix=f".{file_extension}"
        ) as fp:
            fp.write(result.content)
            display_file(
                fp.name, file_url, default_height_if_needed=default_height_if_needed
            )
    else:
        st.error(f"Error fetching file: {result.text}")
