import base64
import json
import mimetypes
import os
import tempfile
from typing import List
from urllib.parse import quote

import pandas as pd
import requests
import streamlit as st

map_languauge_extension = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "java": "java",
    "c": "c",
    "cpp": "cpp",
    "csharp": "csharp",
    "html": "html",
    "css": "css",
    "yaml": "yaml",
    "bash": "bash",
    "sh": "bash",
    "sql": "sql",
    "php": "php",
    "ruby": "ruby",
    "go": "go",
    "rust": "rust",
    "kotlin": "kotlin",
    "swift": "swift",
    "env": "env",
    "toml": "toml",
}
mimes = [
    "text/plain",
    "text/markdown",
    "text/html",
    "text/csv",
    "text/x-python",
    "text/x-r",
    "text/x-sql",
    "text/x-latex",
    "text/x-shellscript",
    "text/x-csrc",
    "text/x-java-source",
    # Documents
    "application/pdf",
    "application/rtf",
    "application/epub+zip",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.ms-excel",
    "application/vnd.ms-powerpoint",
    "application/x-iwork-keynote-sffkey",
    "application/x-iwork-pages-sffpages",
    "application/x-iwork-numbers-sffnumbers",
    # Images
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/tiff",
    "image/bmp",
    "image/svg+xml",
    # Audio
    "audio/mpeg",
    "audio/wav",
    "audio/ogg",
    "audio/flac",
    "audio/aac",
    "audio/x-ms-wma",
    # Video
    "video/mp4",
    "video/avi",
    "video/mov",
    "video/webm",
    "video/x-ms-wmv",
    "video/x-flv",
    "video/mpeg",
    # Archives / disk images
    "application/zip",
    "application/x-7z-compressed",
    "application/x-rar-compressed",
    "application/x-tar",
    "application/gzip",
    "application/x-bzip",
    "application/x-bzip2",
    "application/x-iso9660-image",
    # Code / binaries
    "application/json",
    "application/javascript",
    "application/x-python-code",
    "application/x-httpd-php",
    "application/x-sh",
    "application/x-bash",
    "application/x-csh",
    "application/xml",
    "application/octet-stream",
    "application/x-msdownload",
]
mimes_map = {
    # Text / markup
    "text/plain": "Text",
    "text/markdown": "Markdown File",
    "text/html": "HTML File",
    "text/csv": "CSV File",
    "text/x-python": "Python Script",
    "text/x-r": "R Script",
    "text/x-sql": "SQL Script",
    "text/x-latex": "LaTeX File",
    "text/x-shellscript": "Shell Script",
    "text/x-csrc": "C Source File",
    "text/x-java-source": "Java Source File",
    # Documents
    "application/pdf": "PDF",
    "application/rtf": "RTF Document",
    "application/epub+zip": "EPUB Document",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Word Document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel Spreadsheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "PowerPoint Presentation",
    "application/vnd.ms-excel": "Excel Spreadsheet (Legacy)",
    "application/vnd.ms-powerpoint": "PowerPoint Presentation (Legacy)",
    "application/x-iwork-keynote-sffkey": "Keynote Presentation",
    "application/x-iwork-pages-sffpages": "Pages Document",
    "application/x-iwork-numbers-sffnumbers": "Numbers Spreadsheet",
    # Images
    "image/jpeg": "JPEG Image",
    "image/png": "PNG Image",
    "image/gif": "GIF Image",
    "image/webp": "WebP Image",
    "image/tiff": "TIFF Image",
    "image/bmp": "Bitmap Image",
    "image/svg+xml": "SVG Vector Image",
    # Audio
    "audio/mpeg": "MP3 Audio",
    "audio/wav": "WAV Audio",
    "audio/ogg": "OGG Audio",
    "audio/flac": "FLAC Audio",
    "audio/aac": "AAC Audio",
    "audio/x-ms-wma": "WMA Audio",
    # Video
    "video/mp4": "MP4 Video",
    "video/avi": "AVI Video",
    "video/mov": "MOV Video",
    "video/webm": "WebM Video",
    "video/x-ms-wmv": "WMV Video",
    "video/x-flv": "FLV Video",
    "video/mpeg": "MPEG Video",
    # Archives / disk images
    "application/zip": "ZIP Archive",
    "application/x-7z-compressed": "7z Archive",
    "application/x-rar-compressed": "RAR Archive",
    "application/x-tar": "TAR Archive",
    "application/gzip": "GZ Archive",
    "application/x-bzip": "BZIP Archive",
    "application/x-bzip2": "BZIP2 Archive",
    "application/x-iso9660-image": "ISO Disk Image",
    # Code / binaries
    "application/json": "JSON File",
    "application/javascript": "JavaScript File",
    "application/x-python-code": "Compiled Python Code",
    "application/x-httpd-php": "PHP File",
    "application/x-sh": "Shell Script",
    "application/x-bash": "Bash Script",
    "application/x-csh": "C-Shell Script",
    "application/xml": "XML File",
    "application/octet-stream": "Binary File",
    "application/x-msdownload": "Windows Executable",
}


def get_setting(key: str, default=None):
    result = requests.get(f"http://back:80/settings/{key}")
    if result.status_code == 200:
        return result.json()
    else:
        st.error(f"Failed to retrieve setting {key}: {result.text}")
        return default


def display_file(file_path: str, file_url: str, default_height_if_needed: int = 1000):
    file_url = file_url.replace("http://back:80", "http://localhost:8400")
    file_extension = file_path.split(".")[-1].lower()
    mime = guess_mime(file_path)

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


                if file_extension == "md" or file_extension == "markdown":
                    st.markdown(file_bytes.decode("utf-8"), unsafe_allow_html=True)

                elif file_extension == "json":
                    st.json(json.loads(file_bytes.decode("utf-8")))

                elif file_extension in map_languauge_extension:
                    st.markdown(
                        f"Code: `{map_languauge_extension[file_extension]}`",
                    )
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

                elif mime.startswith("image/"):
                    st.image(file_bytes, use_container_width=True)

                elif mime.startswith("text/"):
                    st.code(
                        file_bytes.decode("utf-8"),
                    )

                elif mime.startswith("audio/"):
                    st.audio(file_bytes, format="audio/wav")

                elif mime.startswith("video/"):
                    st.video(file_bytes, format="video/mp4")

                else:
                    st.error(
                        f"Can't load a preview for this file type. {file_extension} is not supported."
                    )
    except Exception as e:
        st.error(
            f"File might be corrupted or not supported. Error displaying file: {str(e)}"
        )


def download_and_display_file(file_name, default_height_if_needed=1000):
    encoded_file_name = quote(file_name)
    size = requests.get(f"http://back:80/files/metadata/{encoded_file_name}")
    size = size.json().get("size", 0) / (1024 * 1024) if size.status_code == 200 else -1
    size_limit = get_setting("auto_display_file_size_limit")
    if (
        size < 0
        or size < size_limit
        or st.toggle(
            "This file exceeds the size limit. Display anyway?",
            value=False,
            key=f"display_large_file_toggle_{file_name}",
            help=f"The file is over {size_limit:.1f} MB. Toggle to allow display.",
        )
    ):
        with st.spinner("Displaying file...", show_time=True):
            file_url = f"http://back:80/files/download/{encoded_file_name}"
            result = requests.get(file_url)
            if result.status_code != 200:
                return None
            result = result.content

            if result is not None:
                file_extension = os.path.splitext(file_name)[1].lower()
                with tempfile.NamedTemporaryFile(
                    delete=True, suffix=f".{file_extension}"
                ) as fp:
                    fp.write(result)
                    fp.flush()
                    fp.seek(0)
                    display_file(
                        fp.name,
                        f"http://back:80/files/download/{quote(file_name)}",
                        default_height_if_needed,
                    )


def download_file_button(file: str):
    file_name = os.path.basename(file)
    with st.spinner("Preparing file...", show_time=True):
        response = requests.get(f"http://back:80/files/download/{file}")
    if response.status_code == 200:
        with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
            tmp_file.write(response.content)
            tmp_file.flush()
            tmp_file.seek(0)
            st.download_button(
                "📥",
                tmp_file.read(),
                file_name=file_name,
                help="Click to download the file.",
                use_container_width=True,
                key=f"see_download_{file}",
            )


def generate_tag_visual_markdown(name: str, color: str):
    def get_contrasting_text_color(hex_color: str) -> str:
        hex_color = hex_color.lstrip("#")
        r, g, b = [int(hex_color[i : i + 2], 16) for i in (0, 2, 4)]
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        return "black" if luminance > 128 else "white"

    """
    Generate a visual representation of a tag with its name and color.
    """
    text_color = get_contrasting_text_color(color)
    return f"""<span style="background-color:{color}; color:{text_color}; padding:4px 8px; border-radius:6px; font-size:0.9em;">{name}</span>"""


def generate_aside_tag_markdown(names: List[str], colors: List[str]):
    return f"""
    <div style="display: flex; flex-direction: raw; flex-wrap: wrap; gap: 8px; margin: 6px;">
        {''.join(generate_tag_visual_markdown(name, color) for name, color in zip(names, colors))}
    </div>
    """


def generate_project_visual_markdown(name: str, color: str):
    """
    Generate a visual representation of a project with its name and color.
    """
    return f"<span style='color:{color}; font-weight:bold'>{name}</span>"


def generate_aside_project_markdown(names: List[str], colors: List[str]):
    return f"""
    <div style="display: flex; flex-direction: raw; flex-wrap: wrap; gap: 8px; margin: 6px;">
        {''.join(generate_project_visual_markdown(name, color) for name, color in zip(names, colors))}
    </div>
    """


def spacer(space: int = 30):
    """
    Add a spacer to the Streamlit app.
    """
    st.markdown(f"""<div style="margin: {space}px"/>""", unsafe_allow_html=True)


def custom_style():
    """
    Apply custom CSS styles to the Streamlit app.
    """
    st.markdown(
        """
        <style>
        #MainMenu {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def toast_for_rerun(message: str, icon: str = None):
    if "toast_for_rerun" not in st.session_state:
        st.session_state.toast_for_rerun = []
    st.session_state.toast_for_rerun.append((message, icon))


def clear_cache():
    if "explorer_files" in st.session_state:
        del st.session_state.explorer_files
    if "file_to_see" in st.session_state:
        del st.session_state.file_to_see
    if "note_name" in st.session_state:
        del st.session_state.note_name
    if "note_content" in st.session_state:
        del st.session_state.note_content


def guess_mime(file_name: str) -> str:
    """
    Guess the MIME type of a file based on its name, with custom overrides.
    """
    ext = file_name.lower().split('.')[-1]

    custom_mime = {
        "md": "text/markdown",
        "markdown": "text/markdown",
        "env": "text/env",
        "yaml": "text/x-yaml",
        "yml": "text/x-yaml",
        "toml": "text/toml",
        "ipynb": "application/x-ipynb+json",
        "jsonl": "application/x-ndjson",
        "log": "text/log",
        "logs": "text/log",
    }

    if ext in custom_mime:
        return custom_mime[ext]

    mime, _ = mimetypes.guess_type(file_name)
    return mime or "application/octet-stream"