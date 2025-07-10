import json
import logging
import mimetypes
import os
import queue
import time
import traceback
from datetime import datetime

import docx
from controllers.OCRManager import OCRManager
from controllers.TranscriptionManager import TranscriptionManager
from db import Summary, SummaryTask, TaskStateEnum, get_db
from PyPDF2 import PdfReader
from sqlalchemy import and_
from tools.ollama import request_ollama
from views.settings import get_setting


class SummarizeManager:
    in_progress_file = None
    queue = queue.Queue()

    def start_thread():
        db = get_db()
        pending = (
            db.query(SummaryTask)
            .filter(
                SummaryTask.state.in_(
                    [TaskStateEnum.PENDING, TaskStateEnum.IN_PROGRESS]
                )
            )
            .all()
        )
        for task in pending:
            task.state = TaskStateEnum.PENDING
            SummarizeManager.queue.put(task.file)
        db.commit()
        db.close()
        SummarizeManager.loop()

    @classmethod
    def loop(cls):
        time.sleep(10)
        while True:
            time.sleep(1)
            file = cls.queue.get()
            cls.in_progress_file = file

            db = get_db()
            try:
                logging.info(f"SUMMARY >> Processing file: {file}")
                transcription = None
                ocr = None
                content = None
                file_extension = file.split(".")[-1].lower()
                mime, _ = mimetypes.guess_type(file)
                logging.info(
                    f"SUMMARY >> File extension: {file_extension}, MIME type: {mime}"
                )

                # MARK: Image
                if mime.startswith("image/"):
                    logging.info("SUMMARY >> Attempting to get OCR.")
                    result = OCRManager.get(file)
                    if result is None:
                        logging.info("SUMMARY >> No OCR found, re-adding to queue.")
                        cls.queue.put(file)
                        continue
                    ocr = "\n".join(
                        [item[1][0] for item in json.loads(result.get("ocr"))]
                    )
                    blip = result.get("blip")

                # MARK: Audio and Video
                elif mime.startswith("audio/") or mime.startswith("video/"):
                    logging.info("SUMMARY >> Attempting to get transcription.")
                    transcription = TranscriptionManager.get(file)
                    if transcription is None:
                        logging.info(
                            "SUMMARY >> No transcription found, re-adding to queue."
                        )
                        cls.queue.put(file)
                        continue
                    transcription = transcription.get("transcription")

                # MARK: Text and JSON
                elif mime is None or mime.startswith("text") or mime.endswith("json"):
                    logging.info("SUMMARY >> Attempting to read text content.")
                    with open(file, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                # MARK: PDF
                elif mime == "application/pdf":
                    logging.info("SUMMARY >> Attempting to read PDF content.")
                    content = "\n".join(
                        page.extract_text() or "" for page in PdfReader(file).pages
                    )

                # MARK: Word
                elif mime in (
                    "application/msword",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ):
                    logging.info("SUMMARY >> Attempting to read DOCX content.")
                    doc = docx.Document(file)
                    content = "\n".join(p.text for p in doc.paragraphs)

                task = (
                    db.query(SummaryTask)
                    .filter(
                        and_(
                            SummaryTask.file == file,
                            SummaryTask.state == TaskStateEnum.PENDING,
                        )
                    )
                    .order_by(SummaryTask.added.desc())
                    .first()
                )
                task.state = TaskStateEnum.IN_PROGRESS
                db.commit()
                # MARK: Prompt
                if transcription is None and ocr is None and content is None:
                    raise Exception(f"Can't summarize this type of file: {file}")
                else:
                    logging.info("SUMMARY >> Asking LLM for summary.")
                    keywords, summary = cls.make_summary(
                        input=f"""
File Name: {os.path.basename(file)}
File Extension: {file_extension}
MIME Type: {mime if mime else "Not available"}

OCR: {ocr if ocr else "Not available"}
BLIP: {blip if blip else "Not available"}
Transcription: {transcription if transcription else "Not available"}
Content:
{content if content else "Not available"}
"""
                    )
                logging.info(
                    f"SUMMARY >> Result for file {file}: {keywords} - {summary}"
                )

                task.state = TaskStateEnum.COMPLETED
                task.completed = datetime.now()
                task.result = f"{keywords} - {summary}"
                db.query(Summary).filter(Summary.file == file).delete()
                db.add(
                    Summary(
                        file=file,
                        date=datetime.now(),
                        summary=summary,
                        keywords=json.dumps(keywords),
                    )
                )
                db.commit()
                logging.info(f"SUMMARY >> Completed processing for file: {file}")
            except Exception as e:
                db.rollback()
                task = db.query(SummaryTask).filter(SummaryTask.file == file).first()
                if task:
                    task.state = TaskStateEnum.FAILED
                    task.completed = datetime.now()
                    task.result = str(e)
                    db.commit()
                logging.error(f"Error processing summary for file {file}: {str(e)}")
                logging.error(traceback.format_exc())
            finally:
                cls.in_progress_file = None
                db.close()

    @classmethod
    def make_summary(cls, input):
        model = get_setting("summarization_model")
        keywords = request_ollama(
            model=model,
            prompt=""""! FILE CONTENT START !
{input}
! FILE CONTENT END !

! TASK !
You are an expert summarizer.

Extract **5 to 10 relevant keywords** that capture the **main topics and themes** of the file content above.

! FORMAT !
Respond ONLY with a plain comma-separated list.  
Do NOT use JSON, code blocks, quotes, or formatting.  
Example: keyword1, keyword2, keyword3, ...
""",
            input_text=input,
        )
        if keywords.startswith("[") and keywords.endswith("]"):
            keywords = json.loads(keywords)
        else:
            keywords = [w.strip() for w in keywords.split(",")]

        summary = request_ollama(
            model=model,
            prompt=""""! FILE CONTENT START !
{input}
! FILE CONTENT END !

! TASK !
You are an expert summarizer.

Write a **detailed summary** that captures the **essence**, **key points**, and **main insights** from the file content above.

! FORMAT !
Respond ONLY with plain markdown.  
Do NOT include explanations, notes, or any formatting outside the summary itself.
""",
            input_text=input,
        ).strip()
        if summary.startswith("```") and summary.endswith("```"):
            summary = summary[3:-3].strip()
        return (keywords, summary)

    @classmethod
    def add_file_to_queue(cls, file):
        db = get_db()
        try:
            if (
                db.query(SummaryTask)
                .filter(SummaryTask.file == file)
                .filter(
                    SummaryTask.state.in_(
                        [TaskStateEnum.PENDING, TaskStateEnum.IN_PROGRESS]
                    )
                )
                .first()
            ):
                raise Exception(f"File {file} is already in the summary queue.")
            db.add(
                SummaryTask(
                    file=file,
                    added=datetime.now(),
                    state=TaskStateEnum.PENDING,
                )
            )
            db.commit()
            cls.queue.put(file)
        except Exception as e:
            db.rollback()
            logging.error(f"Error adding file {file} to Summary queue: {str(e)}")
            logging.error(traceback.format_exc())
            raise e
        finally:
            db.close()

    @classmethod
    def get(cls, file):
        db = get_db()
        summary = db.query(Summary).filter(Summary.file == file).first()
        db.close()
        if not summary:
            return None
        return {
            "file": summary.file,
            "date": summary.date,
            "summary": summary.summary,
            "keywords": json.loads(summary.keywords),
        }

    @classmethod
    def delete(cls, file):
        """
        Delete the summary and its tasks for a given file.
        """
        db = get_db()
        try:
            summary = db.query(Summary).filter(Summary.file == file).first()
            if summary:
                db.delete(summary)

            tasks = db.query(SummaryTask).filter(SummaryTask.file == file).all()
            for task in tasks:
                db.delete(task)
            db.commit()
        except Exception as e:
            db.rollback()
            logging.error(f"Error deleting summary for file {file}: {str(e)}")
            logging.error(traceback.format_exc())
            raise e
        finally:
            db.close()

    @classmethod
    def move(cls, file, new_file):
        """
        Move the summary and its tasks to a new file.
        """
        db = get_db()
        try:
            summary = db.query(Summary).filter(Summary.file == file).first()
            if summary:
                summary.file = new_file
                db.commit()

            tasks = db.query(SummaryTask).filter(SummaryTask.file == file).all()
            for task in tasks:
                task.file = new_file
            db.commit()
        except Exception as e:
            db.rollback()
            logging.error(
                f"Error moving summary for file {file} to {new_file}: {str(e)}"
            )
            logging.error(traceback.format_exc())
            raise e
        finally:
            db.close()

    @classmethod
    def get_tasks(cls, file):
        db = get_db()
        tasks = db.query(SummaryTask).filter(SummaryTask.file == file).all()
        db.close()

        return [
            {
                "file": task.file,
                "state": task.state.value,
                "added": task.added.strftime("%d-%m-%Y %H:%M:%S"),
                "completed": task.completed.strftime("%d-%m-%Y %H:%M:%S")
                if task.completed
                else None,
                "result": task.result,
            }
            for task in tasks
        ]

    @classmethod
    def list_tasks(cls):
        db = get_db()
        tasks = db.query(SummaryTask).order_by(SummaryTask.added.desc()).all()
        db.close()
        return [
            {
                "file": task.file,
                "state": task.state.value,
                "added": task.added.strftime("%d-%m-%Y %H:%M:%S"),
                "completed": task.completed.strftime("%d-%m-%Y %H:%M:%S")
                if task.completed
                else None,
                "result": task.result,
            }
            for task in tasks
        ]
