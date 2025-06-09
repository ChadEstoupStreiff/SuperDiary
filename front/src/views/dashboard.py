import requests
import streamlit as st


def dashboard():
    """
    Render the dashboard page.
    """
    # cols = st.columns(3)
    # with cols[0]:
    #     st.page_link(explorer, label="🔍 Explorer", use_container_width=True)
    # with cols[1]:
    #     st.page_link(audio_record, label="🎤 Audio Record", use_container_width=True)
    # with cols[2]:
    #     st.page_link(settings, label="⚙️ Settings", use_container_width=True)

    st.write("Welcome to the Super Diary Dashboard!")
    cols = st.columns([2, 1])

    with cols[1]:
        files = st.file_uploader(
            "Upload files",
            accept_multiple_files=True,
            help="Upload files to be processed by the system.",
        )
        if st.button(
            "Upload Files",
            help="Click to upload the selected files.",
            use_container_width=True,
        ):
            if files:
                files_payload = [
                    ("files", (file.name, file, file.type)) for file in files
                ]
                response = requests.post(
                    "http://back:80/files/upload?subdirectory=uploads",
                    files=files_payload,
                )
                if response.status_code == 200:
                    st.success("Files uploaded successfully.")
                else:
                    st.error(f"Failed to upload: {response.text}")
            else:
                st.warning("No files selected for upload.")

        with st.container(border=True):
            st.metric(
                label="Total Files",
                value=requests.get("http://back:80/files/count").json(),
                help="Total number of files processed by the system.",
            )
