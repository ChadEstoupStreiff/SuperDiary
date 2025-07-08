import logging
from threading import Thread

import uvicorn
from controllers.FileManager import FileManager
from controllers.OCRManager import OCRManager
from controllers.SummarizeManager import SummarizeManager
from controllers.TranscriptionManager import TranscriptionManager
from db import DB, create_default_values
from db.models import Base
from fastapi import FastAPI
from pillow_heif import register_heif_opener
from views.ollama import list_models, pull_model
from views.settings import get_setting

app = FastAPI()


import views.files

app.include_router(views.files.router)

import views.calendar

app.include_router(views.calendar.router)

import views.ocr

app.include_router(views.ocr.router)

import views.transcription

app.include_router(views.transcription.router)

import views.summarize

app.include_router(views.summarize.router)

import views.notes

app.include_router(views.notes.router)

import views.ollama

app.include_router(views.ollama.router)

import views.projects

app.include_router(views.projects.router)

import views.tags

app.include_router(views.tags.router)

import views.settings

app.include_router(views.settings.router)


@app.get("/ocr/health")
def ocr_health():
    """
    Health check for the OCR service.
    """
    if ocr_thread.is_alive():
        return "RUNNING"
    else:
        return "DEAD"


@app.get("/transcription/health")
def transcription_health():
    """
    Health check for the transcription service.
    """
    if transcription_thread.is_alive():
        return "RUNNING"
    else:
        return "DEAD"


@app.get("/summarize/health")
def summarize_health():
    """
    Health check for the summarization service.
    """
    if summarize_thread.is_alive():
        return "RUNNING"
    else:
        return "DEAD"


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    Base.metadata.create_all(bind=DB().engine)
    create_default_values()

    FileManager.setup()

    register_heif_opener()
    transcription_thread = Thread(target=TranscriptionManager.start_thread)
    transcription_thread.daemon = True  # Daemonize thread
    transcription_thread.start()

    summarize_thread = Thread(target=SummarizeManager.start_thread)
    summarize_thread.daemon = True  # Daemonize thread
    summarize_thread.start()

    ocr_thread = Thread(target=OCRManager.start_thread)
    ocr_thread.daemon = True  # Daemonize thread
    ocr_thread.start()

    if len(list_models()) == 0:
        pull_model(get_setting("summarization_model"))

    uvicorn.run(app, host="0.0.0.0", port=80)
    ocr_thread.join()  # Wait for the OCR thread to finish
