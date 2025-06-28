import requests
import streamlit as st


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


def settings():
    """
    Settings page for the application.
    This function is a placeholder for the settings view.
    """
    tab_llama, tab_chatgpt, tab_gemini = st.tabs(
        ["Llama (local)", "OpenAI ChatGPT", "Google Gemini"]
    )

    with st.expander("LLM Settings", expanded=True):
        with tab_llama:
            result = requests.get("http://back:80/ollama/list")
            if result.status_code == 200:
                installed_models = [m["name"] for m in result.json()]
            else:
                installed_models = None

                if installed_models is None:
                    st.error(
                        "Failed to fetch installed models. Please try again later."
                    )

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

    st.header("Application Settings")
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


if __name__ == "__main__":
    settings()
