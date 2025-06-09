import streamlit as st


def settings():
    """
    Settings page for the application.
    This function is a placeholder for the settings view.
    """
    with st.expander("OCR Settings", expanded=True):
        st.checkbox("Enable OCR Processing", value=True)

    with st.expander("Summarization Settings", expanded=True):
        st.checkbox("Enable Summarization", value=True)

    with st.expander("Transcription Settings", expanded=True):
        st.checkbox("Enable Transcription", value=True)
        st.radio(
            "Transcription model",
            options=["tiny", "base", "small", "medium", "large-v3"],
            index=2,
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
