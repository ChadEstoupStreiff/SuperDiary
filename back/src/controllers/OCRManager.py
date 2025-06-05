import logging
import queue
import traceback
from datetime import datetime

from db import OCR, OCRTask, TaskStateEnum, get_db


class OCRManager:
    in_progess_file = None
    queue = queue.Queue()

    def start_thread():
        """
        Start the OCR processing thread.
        This method should be implemented to handle the OCR processing logic.
        """
        db = get_db()
        pending = db.query(OCRTask).filter(OCRTask.state == TaskStateEnum.PENDING).all()
        db.close()
        for task in pending:
            OCRManager.queue.put(task.file)

        OCRManager.loop()

    @classmethod
    def loop(cls):
        while True:
            file = cls.queue.get()
            cls.in_progess_file = file
            logging.info(f"OCR >> Processing for file: {file}")

            # TODO implement OCR processing logic
            result = "coucou"

            logging.info(f"OCR >> Result for file {file}: {result}")

            db = get_db()
            try:
                ocr_task = db.query(OCRTask).filter(OCRTask.file == file).first()
                if ocr_task:
                    ocr_task.state = TaskStateEnum.COMPLETED
                    db.add(
                        OCR(
                            file=file,
                            date=datetime.now(),
                            ocr=result,
                        )
                    )
                    db.commit()
                logging.info(f"OCR >> Completed processing for file: {file}")
            except Exception as e:
                db.rollback()
                ocr_task = db.query(OCRTask).filter(OCRTask.file == file).first()
                if ocr_task:
                    ocr_task.state = TaskStateEnum.FAILED
                    ocr_task.error_message = str(e)
                    db.commit()
                logging.error(f"Error processing OCR for file {file}: {str(e)}")
                logging.error(traceback.format_exc())
                raise e
            finally:
                cls.in_progess_file = None
                db.close()

    @classmethod
    def add_files_to_queue(cls, file):
        db = get_db()
        try:
            db.add(
                OCRTask(
                    file=file,
                    added=datetime.now(),
                    state=TaskStateEnum.PENDING,
                )
            )
            db.commit()
            cls.queue.put(file)
        except Exception as e:
            db.rollback()
            logging.error(f"Error adding file {file} to OCR queue: {str(e)}")
            logging.error(traceback.format_exc())
            raise e
        finally:
            db.close()

    @classmethod
    def get(cls, file):
        """
        Get the OCR result for a file.
        """
        db = get_db()
        ocr = db.query(OCR).filter(OCR.file == file).first()
        db.close()
        if not ocr:
            raise Exception("OCR not found for this file.")
        return {
            "file": ocr.file,
            "date": ocr.date,
            "ocr": ocr.ocr,
        }

    @classmethod
    def get_tasks(cls, file):
        """
        Get the OCR task state for a file.
        """
        if file == cls.in_progess_file:
            return {
                "state": "IN_PROGRESS",
            }

        db = get_db()
        ocr_tasks = db.query(OCRTask).filter(OCRTask.file == file).all()
        db.close()
        if not ocr_tasks:
            raise Exception("OCR task not found for this file.")

        return [
            {
                "file": ocr_task.file,
                "state": ocr_task.state.value,
                "added": ocr_task.added.strftime("%d-%m-%Y %H:%M:%S"),
                "completed": ocr_task.completed.strftime("%d-%m-%Y %H:%M:%S")
                if ocr_task.completed
                else None,
                "error_message": ocr_task.error_message,
            }
            for ocr_task in ocr_tasks
        ]

    @classmethod
    def list_tasks(cls):
        """
        Get all OCR tasks.
        """
        db = get_db()
        ocr_tasks = db.query(OCRTask).order_by(OCRTask.added).all()
        db.close()
        return [
            {
                "file": task.file,
                "state": task.state.value,
                "added": task.added.strftime("%d-%m-%Y %H:%M:%S"),
                "completed": task.completed.strftime("%d-%m-%Y %H:%M:%S")
                if task.completed
                else None,
                "error_message": task.error_message,
            }
            for task in ocr_tasks
        ]
