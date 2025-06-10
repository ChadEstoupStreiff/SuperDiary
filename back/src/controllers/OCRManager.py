import logging
import queue
import subprocess
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

            db = get_db()
            try:
                task = db.query(OCRTask).filter(OCRTask.file == file).first()
                task.state = TaskStateEnum.IN_PROGRESS
                db.commit()

                logging.info(f"OCR >> Processing for file: {file}")
                proc = subprocess.run(
                    ["python3", "/app/tesseract.py", file],
                    capture_output=True,
                    text=True,
                )
                if proc.returncode != 0:
                    raise RuntimeError(
                        f"Subprocess failed with code {proc.returncode}: {proc.stderr.strip()}"
                    )
                result = proc.stdout.strip()
                logging.info(f"OCR >> Result for file {file}: {result}")

                task.state = TaskStateEnum.COMPLETED
                task.completed = datetime.now()
                task.result = result
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
                task = db.query(OCRTask).filter(OCRTask.file == file).first()
                if task:
                    task.state = TaskStateEnum.FAILED
                    task.completed = datetime.now()
                    task.result = str(e)
                    db.commit()
                logging.error(f"Error processing OCR for file {file}: {str(e)}")
                logging.error(traceback.format_exc())
            finally:
                cls.in_progess_file = None
                db.close()

    @classmethod
    def add_file_to_queue(cls, file):
        db = get_db()
        try:
            if (
                db.query(OCRTask)
                .filter(OCRTask.file == file)
                .filter(
                    OCRTask.state.in_(
                        [TaskStateEnum.PENDING, TaskStateEnum.IN_PROGRESS]
                    )
                )
                .first()
            ):
                raise Exception(f"File {file} is already in the OCR queue.")
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
    def delete(cls, file):
        """
        Delete the OCR result for a file.
        """
        db = get_db()
        try:
            ocr = db.query(OCR).filter(OCR.file == file).first()
            if ocr:
                db.delete(ocr)

            tasks = db.query(OCRTask).filter(OCRTask.file == file).all()
            for task in tasks:
                db.delete(task)
            db.commit()
        except Exception as e:
            db.rollback()
            logging.error(f"Error deleting OCR for file {file}: {str(e)}")
            logging.error(traceback.format_exc())
            raise e
        finally:
            db.close()

    @classmethod
    def move(cls, file, new_file):
        """
        Move the OCR result for a file to a new file.
        """
        db = get_db()
        try:
            ocr = db.query(OCR).filter(OCR.file == file).first()
            if ocr:
                ocr.file = new_file
                db.commit()

            tasks = db.query(OCRTask).filter(OCRTask.file == file).all()
            for task in tasks:
                task.file = new_file
            db.commit()
        except Exception as e:
            db.rollback()
            logging.error(f"Error moving OCR for file {file} to {new_file}: {str(e)}")
            logging.error(traceback.format_exc())
            raise e
        finally:
            db.close()

    @classmethod
    def get_tasks(cls, file):
        """
        Get the OCR task state for a file.
        """

        db = get_db()
        ocr_tasks = db.query(OCRTask).filter(OCRTask.file == file).all()
        db.close()
        if not ocr_tasks:
            raise Exception("OCR task not found for this file.")

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
            for task in ocr_tasks
        ]

    @classmethod
    def list_tasks(cls):
        """
        Get all OCR tasks.
        """
        db = get_db()
        ocr_tasks = db.query(OCRTask).order_by(OCRTask.added.desc()).all()
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
            for task in ocr_tasks
        ]
