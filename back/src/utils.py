import json
import logging
import mimetypes
import os

import docx
from controllers.OCRManager import OCRManager
from controllers.TranscriptionManager import TranscriptionManager
from controllers.NoteManager import NoteManager
from PyPDF2 import PdfReader


def guess_mime(file_name: str) -> str:
    """
    Guess the MIME type of a file based on its name, with custom overrides.
    """
    ext = file_name.lower().split(".")[-1]

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
        return custom_mime[ext].strip()

    mime, _ = mimetypes.guess_type(file_name)
    return mime.strip() or "application/octet-stream"


def read_content(file: str, force_read: bool = False) -> str:
    """
    Read the content of a file and return it as a string.
    """
    content = None

    mime = guess_mime(file)
    # MARK: Image
    if mime.startswith("image/"):
        result = OCRManager.get(file)
        if result is not None:
            ocr = "\n".join([item[1][0] for item in json.loads(result.get("ocr"))])
            blip = result.get("blip")
            if ocr and blip:
                content = f"CAPTION: {blip}\nOCR: {ocr}"

    # MARK: Audio and Video
    elif mime.startswith("audio/") or mime.startswith("video/"):
        logging.info("SUMMARY >> Attempting to get transcription.")
        transcription = TranscriptionManager.get(file)
        if transcription is not None:
            transcription = transcription.get("transcription")
            if transcription:
                content = f"Transcription: {transcription}"

    # MARK: Text and JSON
    elif mime.startswith("text") or mime.endswith("json"):
        logging.info("SUMMARY >> Attempting to read text content.")
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

    # MARK: PDF
    elif mime == "application/pdf":
        logging.info("SUMMARY >> Attempting to read PDF content.")
        content = "\n".join(page.extract_text() or "" for page in PdfReader(file).pages)

    # MARK: Word
    elif mime in (
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ):
        logging.info("SUMMARY >> Attempting to read DOCX content.")
        doc = docx.Document(file)
        content = "\n".join(p.text for p in doc.paragraphs)

    elif force_read:
        with open(file, "r") as f:
            content = f.read()

    note = NoteManager.get(file)
    if note is not None:
        note = note.get("content")
    else:
        note = None

    if content is None:
        logging.warning(f"Unable to read content from file: {file}")
        return None

    date = file.split("/")[1]
    subfolder = file.split("/")[2]
    return f"""
File Name: {os.path.basename(file)}
File Extension: {os.path.splitext(file)[1]}
MIME Type: {mime if mime else "Unknown"}
Date: {date}
Subfolder: {subfolder}

{f"Note: {note}\n" if note else ""}
Content:
{content if content else "Can't read"}
"""
