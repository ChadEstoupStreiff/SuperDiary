import logging
import mimetypes
import os
import time
from datetime import datetime
from typing import List

from controllers.SummarizeManager import SummarizeManager
from tqdm import tqdm
from whoosh import writing
from whoosh.fields import DATETIME, TEXT, Schema
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
            file=TEXT(stored=True),
            file_name=TEXT(stored=True),
            mime=TEXT(stored=True),
            date=DATETIME(stored=True, sortable=True),
            subfolder=TEXT(stored=True),
            keywords=TEXT(stored=True),
            summary=TEXT(stored=True),
            # content=TEXT(stored=True),  # Use None for raw text
        )

        if not os.path.exists("/data/index"):
            os.makedirs("/data/index", exist_ok=True)
        cls.ix = create_in("/data/index", cls.schema)
        logging.info("FileManager >> Setup complete.")
        cls.index_files()

    @classmethod
    def index_files(cls):
        start_time = time.time()
        logging.info("FileManager >> Indexing files...")
        if not cls.ix:
            raise Exception("Index not initialized. Call setup() first.")
        writer = cls.ix.writer()
        writer.mergetype = writing.CLEAR  # clear existing index
        count = 0

        for dp, _, filenames in tqdm(
            os.walk("/shared"), desc="Indexing files", unit="file"
        ):
            for filename in filenames:
                if filename != ".DS_Store":
                    file = os.path.join(dp, filename)
                    date = file.split("/")[2]
                    subfolder = file.split("/")[3]
                    summary = SummarizeManager.get(file)
                    if summary is None:
                        summary = ""
                        keywords = ""
                    else:
                        keywords = summary.get("keywords", [])
                        summary = summary.get("summary", "")
                    mime_file, _ = mimetypes.guess_type(file)
                    writer.add_document(
                        file=file,
                        file_name=filename,
                        mime=mime_file or "application/octet-stream",
                        date=datetime.fromisoformat(date),
                        subfolder=subfolder,
                        keywords=",".join(keywords) if keywords else "",
                        summary=summary,
                    )
                    count += 1

        writer.commit()
        logging.info(
            f"FileManager >> Indexed {count} files in {time.time() - start_time:.2f} seconds."
        )

    @classmethod
    def search_files(
        cls,
        text: str = None,
        start_date: str = None,
        end_date: str = None,
        types: List[list] = None,
    ):
        logging.critical(
            f"Search files with text: {text}, start_date: {start_date}, end_date: {end_date}, types: {types}"
        )
        start = time.time()
        if not cls.ix:
            raise RuntimeError("Index not initialised")
        cls.index_files()

        with cls.ix.searcher() as searcher:
            parser = MultifieldParser(
                ["file_name", "keywords", "summary"], schema=cls.schema, group=OrGroup
            )

            query = parser.parse(text) if text else Every()
            results = searcher.search(query, limit=None)

            start_dt = (
                datetime.fromisoformat(start_date.replace("T", " "))
                if start_date
                else None
            )
            end_dt = (
                datetime.fromisoformat(end_date.replace("T", " ")) if end_date else None
            )

            filtered = []
            for r in results:
                r_date = r.get("date")
                if isinstance(r_date, str):
                    r_date = datetime.fromisoformat(r_date)

                if (
                    (start_dt <= r_date if start_dt else True)
                    and (r_date <= end_dt if end_dt else True)
                    and (not types or r.get("mime") in types)
                ):
                    filtered.append(r.get("file"))

            logging.info(
                f"FileManager >> Search completed with {len(filtered)} files in {time.time() - start:.2f} seconds."
            )
            return filtered

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
