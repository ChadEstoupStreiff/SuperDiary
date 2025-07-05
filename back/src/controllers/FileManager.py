import logging
import mimetypes
import os
import time
from datetime import datetime
from typing import List

from controllers.NoteManager import NoteManager
from controllers.SummarizeManager import SummarizeManager
from db import get_db
from db.models import ProjectFile, TagFile
from tqdm import tqdm
from views.settings import get_setting
from whoosh import writing
from whoosh.fields import ID, NGRAM, Schema
from whoosh.index import create_in
from whoosh.qparser import MultifieldParser, OrGroup
from whoosh.query import Every


class FileManager:
    schema = None
    ix = None

    @classmethod
    def setup(cls):
        logging.info("FileManager >> Setting up...")
        cls.schema = Schema(
            file=ID(stored=True),  # exact match only, fast and compact
            file_name=NGRAM(minsize=3, maxsize=7, stored=True),  # used in query
            # mime=ID(stored=True),  # filter only
            # date=DATETIME(stored=True, sortable=True),  # filter only
            # subfolder=ID(stored=True),  # filter only
            keywords=NGRAM(minsize=3, maxsize=5, stored=True),  # used in query
            summary=NGRAM(minsize=3, maxsize=5, stored=True),  # used in query
            note=NGRAM(minsize=3, maxsize=5, stored=True),  # used in query
        )

        if not os.path.exists("/data/index"):
            os.makedirs("/data/index", exist_ok=True)
        cls.ix = create_in("/data/index", cls.schema)
        logging.info("FileManager >> Setup complete.")

    @classmethod
    def index_files(
        cls,
        start_date: str = None,
        end_date: str = None,
        subfolders: List[str] = None,
        types: List[list] = None,
        projects: List[str] = None,
        tags: List[str] = None,
    ):
        if not cls.ix:
            raise Exception("Index not initialized. Call setup() first.")
        writer = cls.ix.writer()
        writer.mergetype = writing.CLEAR  # clear existing index
        count = 0

        start_dt = (
            datetime.fromisoformat(start_date.replace("T", " ")) if start_date else None
        )
        end_dt = (
            datetime.fromisoformat(end_date.replace("T", " ")) if end_date else None
        )
        for dp, _, filenames in tqdm(
            os.walk("/shared"), desc="Indexing files", unit="file"
        ):
            try:
                for filename in filenames:
                    file = os.path.join(dp, filename)
                    mime_file, _ = mimetypes.guess_type(file)
                    mime_file = mime_file or "application/octet-stream"
                    date = datetime.fromisoformat(file.split("/")[2])
                    subfolder = file.split("/")[3]

                    if (
                        filename != ".DS_Store"
                        and (start_dt <= date if start_dt else True)
                        and (date <= end_dt if end_dt else True)
                        and (not types or mime_file in types)
                        and (not subfolders or subfolder in subfolders)
                    ):
                        if projects or tags:
                            db = get_db()
                        try:
                            if projects:
                                file_projects = [
                                    p.project
                                    for p in db.query(ProjectFile)
                                    .filter(ProjectFile.file == file)
                                    .all()
                                ]
                            if tags:
                                file_tags = [
                                    t.tag
                                    for t in db.query(TagFile)
                                    .filter(TagFile.file == file)
                                    .all()
                                ]
                        except Exception as e:
                            logging.error(f"Error querying database: {str(e)}")
                            raise RuntimeError(f"Error querying database: {str(e)}")
                        finally:
                            if projects or tags:
                                db.close()

                        if (
                            not projects or any(p in file_projects for p in projects)
                        ) and (not tags or any(t in file_tags for t in tags)):
                            summary = SummarizeManager.get(file)
                            if summary is None:
                                summary = ""
                                keywords = ""
                            else:
                                keywords = summary.get("keywords", [])
                                summary = summary.get("summary", "")

                            note = NoteManager.get(file)
                            note = note.get("note", "") if note else ""
                            writer.add_document(
                                file=file,
                                file_name=filename,
                                # mime=mime_file or "application/octet-stream",
                                # date=date,
                                # subfolder=subfolder,
                                keywords=",".join(keywords) if keywords else "",
                                summary=summary,
                                note=note,
                            )
                            count += 1
            except Exception as e:
                logging.error(f"Error during search: {str(e)}")
                raise RuntimeError(f"Error during search: {str(e)}")

        writer.commit()

    @classmethod
    def search_files(
        cls,
        text: str = None,
        start_date: str = None,
        end_date: str = None,
        subfolders: List[str] = None,
        types: List[list] = None,
        projects: List[str] = None,
        tags: List[str] = None,
    ):
        start = time.time()
        if not cls.ix:
            raise RuntimeError("Index not initialised")
        cls.index_files(
            start_date=start_date,
            end_date=end_date,
            subfolders=subfolders,
            types=types,
            projects=projects,
            tags=tags,
        )

        with cls.ix.searcher() as searcher:
            parser = MultifieldParser(
                ["file_name", "keywords", "summary", "note"],
                schema=cls.schema,
                group=OrGroup,
            )

            if text:
                query = parser.parse(text)
            else:
                query = Every()

            results = searcher.search(query, limit=get_setting("search_limit"))
            return [r.get("file") for r in results]

    @classmethod
    def get_indexed_files(cls):
        if not cls.ix:
            raise Exception("Index not initialized.")

        with cls.ix.searcher() as searcher:
            return [
                searcher.stored_fields(docnum)
                for docnum in range(searcher.doc_count_all())
            ]

    @classmethod
    def get_nbr_indexed_files(cls):
        if not cls.ix:
            raise Exception("Index not initialized.")

        with cls.ix.searcher() as searcher:
            return searcher.doc_count_all()
