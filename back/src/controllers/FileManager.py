import logging
import os
from datetime import datetime
from typing import List

from controllers.NoteManager import NoteManager
from controllers.SummarizeManager import SummarizeManager
from db import get_db
from db.models import ProjectFile, TagFile
from tqdm import tqdm
from utils import guess_mime, read_content
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
            keywords=NGRAM(minsize=3, maxsize=5, stored=False),  # used in query
            summary=NGRAM(minsize=3, maxsize=5, stored=False),  # used in query
            note=NGRAM(minsize=3, maxsize=5, stored=False),  # used in query
            content=NGRAM(minsize=3, maxsize=5, stored=False),  # used in query
        )

        if not os.path.exists("/data/index"):
            os.makedirs("/data/index", exist_ok=True)
        cls.ix = create_in("/data/index", cls.schema)
        logging.info("FileManager >> Setup complete.")

    @classmethod
    def list_files(
        cls,
        start_date: str = None,
        end_date: str = None,
        subfolders: List[str] = None,
        types: List[str] = None,
        projects: List[str] = None,
        tags: List[str] = None,
        exclude_file_types: bool = False,
        exclude_subfolders: bool = False,
        exclude_projects: bool = False,
        exclude_tags: bool = False,
    ):
        files = []

        start_dt = (
            datetime.fromisoformat(start_date.replace("T", " ")) if start_date else None
        )
        end_dt = (
            datetime.fromisoformat(end_date.replace("T", " ")) if end_date else None
        )

        if projects or tags:
            db = get_db()

        try:
            for dp, _, filenames in tqdm(
                os.walk("/shared"), desc="Indexing files", unit="file"
            ):
                for filename in filenames:
                    if filename == ".DS_Store":
                        continue

                    file = os.path.join(dp, filename)
                    mime_file = guess_mime(file) or "application/octet-stream"

                    try:
                        date = datetime.fromisoformat(file.split("/")[2])
                    except Exception:
                        continue  # skip if date parsing fails

                    subfolder = file.split("/")[3]

                    # --- Handle file type filter (with exclude) ---
                    if types:
                        if exclude_file_types:
                            if mime_file in types:
                                continue
                        else:
                            if mime_file not in types:
                                continue

                    # --- Handle subfolder filter (with exclude) ---
                    if subfolders:
                        if exclude_subfolders:
                            if subfolder in subfolders:
                                continue
                        else:
                            if subfolder not in subfolders:
                                continue

                    # --- Handle date range ---
                    if start_dt and date < start_dt:
                        continue
                    if end_dt and date > end_dt:
                        continue

                    file_projects, file_tags = [], []

                    # --- Handle project filter (with exclude) ---
                    if projects:
                        file_projects = [
                            p.project
                            for p in db.query(ProjectFile)
                            .filter(ProjectFile.file == file)
                            .all()
                        ]
                        if exclude_projects:
                            if any(p in file_projects for p in projects):
                                continue
                        else:
                            if not any(p in file_projects for p in projects):
                                continue

                    # --- Handle tag filter (with exclude) ---
                    if tags:
                        file_tags = [
                            t.tag
                            for t in db.query(TagFile)
                            .filter(TagFile.file == file)
                            .all()
                        ]
                        if exclude_tags:
                            if any(t in file_tags for t in tags):
                                continue
                        else:
                            if not any(t in file_tags for t in tags):
                                continue

                    files.append(file)

        except Exception as e:
            logging.error(f"Error querying database: {str(e)}")
            raise RuntimeError(f"Error querying database: {str(e)}")

        finally:
            if projects or tags:
                db.close()

        return files

    @classmethod
    def index_files(cls, files, search_mode: int = 0):
        if not cls.ix:
            raise Exception("Index not initialized. Call setup() first.")
        writer = cls.ix.writer()
        writer.mergetype = writing.CLEAR  # clear existing index
        count = 0

        for file in files:
            filename = os.path.basename(file)
            dp = os.path.dirname(file)

            file = os.path.join(dp, filename)
            mime_file = guess_mime(file)
            mime_file = mime_file or "application/octet-stream"

            content = ""
            summary = ""
            keywords = []

            summary_keywords = SummarizeManager.get(file)
            if summary_keywords is not None:
                # Always keywords
                keywords = summary_keywords.get("keywords", [])

                if search_mode != 0:
                    # Summary only if search mode is NORMAL or DEEP
                    summary = summary_keywords.get("summary", "")

            if search_mode == 2:
                # Read content only if search mode is DEEP
                content = read_content(file, force_read=True)

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
                content=content,
            )
            count += 1

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
        search_mode: int = 0,
        exclude_file_types: bool = False,
        exclude_subfolders: bool = False,
        exclude_projects: bool = False,
        exclude_tags: bool = False,
    ):
        files = cls.list_files(
            start_date=start_date,
            end_date=end_date,
            subfolders=subfolders,
            types=types,
            projects=projects,
            tags=tags,
            exclude_file_types=exclude_file_types,
            exclude_subfolders=exclude_subfolders,
            exclude_projects=exclude_projects,
            exclude_tags=exclude_tags,
        )
        if text:
            text = text.strip()
            if not cls.ix:
                raise RuntimeError("Index not initialised")
            cls.index_files(files, search_mode=search_mode)

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
        else:
            return files

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
