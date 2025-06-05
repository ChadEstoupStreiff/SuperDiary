import os

import requests
import streamlit as st
import pandas as pd
import io


def box_file(file):
    with st.container(border=True):
        preview = st.container(
            border=True,
        )
        file_name = os.path.basename(file)
        date = file.split("/")[1]
        subfolder = file.split("/")[2]
        st.markdown(f"#### {file_name}")
        st.caption(f"**Date:** {date}")
        st.caption(f"**Subfolder:** {subfolder}")
        st.caption(f"**Path:** {file}")

        st.button(
            "View Details",
            key=f"view_details_{file}",
            on_click=lambda: st.write("coucou"),
            help="Click to view file details.",
        )
    return preview


def explorer():
    """
    This function serves as a placeholder for the explorer view.
    It currently does not perform any operations or return any data.
    """
    st.write("Welcome to the Super Diary Explorer!")
    nbr_of_files_per_line = st.sidebar.slider(
        "Number of files per line",
        min_value=1,
        max_value=6,
        value=3,
        help="Adjust the number of files displayed per line.",
    )

    files = requests.get("http://back:80/files/list").json()
    if files:
        st.write("Files in the system:")

        file_preview_containers = []
        for i in range(0, len(files), nbr_of_files_per_line):
            cols = st.columns(nbr_of_files_per_line)
            for j, file in enumerate(files[i : i + nbr_of_files_per_line]):
                with cols[j]:
                    file_preview_containers.append(box_file(file))
        for i in range(len(file_preview_containers)):
            with file_preview_containers[i]:
                if (
                    files[i].endswith(".png")
                    or files[i].endswith(".jpg")
                    or files[i].endswith(".jpeg")
                    or files[i].endswith(".gif")
                    or files[i].endswith(".bmp")
                    or files[i].endswith(".webp")
                ):
                    image = requests.get(f"http://back:80/files/download/{files[i]}")
                    st.image(
                        image.content, use_container_width=True, caption="Image Preview"
                    )
                elif files[i].endswith(".pdf"):
                    pdf_url = f"http://back:80/files/download/{files[i]}"
                    st.markdown(
                        f'<a href="{pdf_url}" target="_blank">View PDF</a>',
                        unsafe_allow_html=True,
                    )
                elif files[i].endswith(".txt"):
                    text = requests.get(f"http://back:80/files/download/{files[i]}").text
                    st.text_area(
                        "Text Preview",
                        value=text,
                        height=200,
                        help="Preview of the text file.",
                    )
                elif files[i].endswith(".csv"):
                    csv_data = requests.get(f"http://back:80/files/download/{files[i]}").text
                    st.dataframe(
                        pd.read_csv(io.StringIO(csv_data)),
                        use_container_width=True,
                        help="Preview of the CSV file.",
                    )
                elif files[i].endswith(".json"):
                    json_data = requests.get(f"http://back:80/files/download/{files[i]}")
                    st.json(json_data)
                elif files[i].endswith(".mp3") or files[i].endswith(".wav"):
                    audio_url = f"http://back:80/files/download/{files[i]}"
                    st.audio(audio_url, format="audio/wav")
                elif files[i].endswith(".mp4") or files[i].endswith(".avi"):
                    video_url = f"http://back:80/files/download/{files[i]}"
                    st.video(video_url)
                else:
                    st.error("Can't load a preview for this file type.")
    else:
        st.write("No files found in the system.")
