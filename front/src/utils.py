import base64
import json
import mimetypes
import os
import tempfile
from urllib.parse import quote

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

# ---------- Friendly labels ----------
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


# TODO cache ?
def download_file(raw_file_name: str):
    """
    Download and cache the file content.
    """
    encoded_file_name = quote(raw_file_name)
    file_url = f"http://back:80/files/download/{encoded_file_name}"
    result = requests.get(file_url)
    return result.content if result.status_code == 200 else None


def download_and_display_file(file_name, default_height_if_needed=1000):
    with st.spinner("Downloading file..."):
        result = download_file(file_name)

    if result is not None:
        file_extension = os.path.splitext(file_name)[1].lower()
        with tempfile.NamedTemporaryFile(
            delete=True, suffix=f".{file_extension}"
        ) as fp:
            fp.write(result)
            display_file(
                fp.name,
                f"http://back:80/files/download/{quote(file_name)}",
                default_height_if_needed,
            )


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


def clear_cache():
    if "explorer_files" in st.session_state:
        del st.session_state.explorer_files
    if "file_to_see" in st.session_state:
        del st.session_state.file_to_see


def toast_for_rerun(message: str, icon: str = None):
    if "toast_for_rerun" not in st.session_state:
        st.session_state.toast_for_rerun = []
    st.session_state.toast_for_rerun.append((message, icon))


def generate_tag_visual_markdown(name: str, color: str):
    def get_contrasting_text_color(hex_color: str) -> str:
        hex_color = hex_color.lstrip("#")
        r, g, b = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
        luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b)
        return "black" if luminance > 128 else "white"

    """
    Generate a visual representation of a tag with its name and color.
    """
    text_color = get_contrasting_text_color(color)
    return f"""<span style="background-color:{color}; color:{text_color}; padding:4px 8px; border-radius:6px; font-size:0.9em;">{name}</span>"""
