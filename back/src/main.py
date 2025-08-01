import logging
import time
from threading import Thread
import traceback

import uvicorn
from controllers.SummarizeManager import SummarizeManager
from controllers.ChatManager import ChatManager
from controllers.FileManager import FileManager
from controllers.OCRManager import OCRManager
from controllers.TranscriptionManager import TranscriptionManager
from db import DB, create_default_values, get_db, TagFile, ProjectFile
from db.models import Base
from utils import walk_files
from fastapi import FastAPI
from pillow_heif import register_heif_opener
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

app = FastAPI()


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        if duration > 0.1:
            logging.critical(
                f"{request.method} {request.url.path} {response.status_code} - {duration:.3f} ms"
            )
        return response


app.add_middleware(LoggingMiddleware)

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

import views.stockpile

app.include_router(views.stockpile.router)

import views.chat

app.include_router(views.chat.router)

import views.utils

app.include_router(views.utils.router)

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

# @app.get("/metrics")
# def metrics():
#     files = walk_files()
#     db = get_db()
#     try:
#         # Count files per project
#         files_per_project = dict(
#             db.query(ProjectFile.project, func.count(ProjectFile.file))
#             .group_by(ProjectFile.project)
#             .all()
#         )

#         # Count files per tag
#         files_per_tag = dict(
#             db.query(TagFile.tag, func.count(TagFile.file))
#             .group_by(TagFile.tag)
#             .all()
#         )

#         # Set of all file names
#         all_files = set(files)

#         # Files with tags
#         tagged_files = set(row[0] for row in db.query(TagFile.file).distinct())

#         # Files in projects
#         project_files = set(row[0] for row in db.query(ProjectFile.file).distinct())

#         # Files with no tag or no project
#         no_tag = list(all_files - tagged_files)
#         no_project = list(all_files - project_files)

#     except Exception as e:
#         logging.error(f"Error retrieving metrics: {str(e)}")
#         db.rollback()
#         logging.error(traceback.format_exc())
#         return {"error": str(e)}
#     finally:
#         db.close()

#     return {
#         "nbr_files": len(files),
#         "files_per_project": files_per_project,
#         "files_per_tag": files_per_tag,
#         "files_without_tag": len(no_tag),
#         "files_without_project": len(no_project),
#     }

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

    chat_thread = Thread(target=ChatManager.start_thread)
    chat_thread.daemon = True  # Daemonize thread
    chat_thread.start()

    # if len(list_models()) == 0:
    #     pull_model(get_setting("summarization_model"))

    uvicorn.run(app, host="0.0.0.0", port=80)
