import requests
import streamlit as st
from utils import clear_cache

def audio_record():
    audio_data = st.audio_input(
        label="Record Audio",
        key="audio_recorder",
    )
    date = st.date_input(
        "Select Date",
        help="Choose the date for the recorded audio.",
        key="audio_date",
    )

    if st.button("Save recorded audio", use_container_width=True):
        if audio_data:
            files_payload = [
                (
                    "files",
                    (f"audio_{date.strftime('%Y-%m-%d')}.wav", audio_data, "audio/wav"),
                )
            ]
            response = requests.post(
                "http://back:80/files/upload?subdirectory=audio&date=" + date,
                files=files_payload,
            )
            if response.status_code == 200:
                st.toast(
                    "Audio recorded and uploaded successfully!",
                    icon="🆕",
                )
                clear_cache()
            else:
                st.toast(
                    "Failed to upload audio. Please try again.",
                    icon="❌",
                )
        else:
            st.warning("No audio recorded yet. Please record audio first.")


if __name__ == "__main__":
    audio_record()
