import logging
import queue
import traceback
from datetime import datetime

from db import Summary, SummaryTask, TaskStateEnum, get_db
import json

class SummarizeManager:
    in_progress_file = None
    queue = queue.Queue()

    def start_thread():
        db = get_db()
        pending = (
            db.query(SummaryTask)
            .filter(SummaryTask.state == TaskStateEnum.PENDING)
            .all()
        )
        db.close()
        for task in pending:
            SummarizeManager.queue.put(task.file)
        SummarizeManager.loop()

    @classmethod
    def loop(cls):
        while True:
            file = cls.queue.get()
            cls.in_progress_file = file

            db = get_db()
            try:
                task = (
                    db.query(SummaryTask)
                    .filter(SummaryTask.file == file)
                    .order_by(SummaryTask.added.desc())
                    .first()
                )
                task.state = TaskStateEnum.IN_PROGRESS
                db.commit()

                logging.info(f"SUMMARY >> Processing file: {file}")
                # TODO: Implement summarization logic
                summary = "summary content"
                keywords = ["keyword1", "keyword2"]
                logging.info(f"SUMMARY >> Result for file {file}: {keywords} - {summary}")

                task.state = TaskStateEnum.COMPLETED
                task.completed = datetime.now()
                task.result = f"{keywords} - {summary}"
                db.add(
                    Summary(
                        file=file,
                        date=datetime.now(),
                        summary=summary,
                        keywords=json.dumps(keywords)
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
            raise Exception("Summary not found for this file.")
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
        if not tasks:
            raise Exception("Summary task not found for this file.")

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
