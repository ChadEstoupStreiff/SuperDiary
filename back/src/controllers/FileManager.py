import logging
import os

from tqdm import tqdm
from whoosh.fields import TEXT, Schema
from whoosh.index import create_in
from whoosh.qparser import MultifieldParser


class FileManager:
    schema = None
    ix = None

    @classmethod
    def setup(cls):
        logging.info("FileManager >> Setting up...")
        cls.schema = Schema(
            file=TEXT(stored=True),
            file_name=TEXT(stored=True),
        )

        if not os.path.exists("/data/index"):
            os.makedirs("/data/index", exist_ok=True)
        cls.ix = create_in("/data/index", cls.schema)
        logging.info("FileManager >> Setup complete.")
        cls.index_files()

    @classmethod
    def index_files(cls):
        logging.info("FileManager >> Indexing files...")
        writer = cls.ix.writer()
        count = 0

        for dp, _, filenames in tqdm(
            os.walk("/shared"), desc="Indexing files", unit="file"
        ):
            for filename in filenames:
                file = os.path.join(dp, filename)
                writer.add_document(
                    file=file,
                    file_name=filename,
                )
                count += 1

        writer.commit()
        logging.info(f"FileManager >> Indexed {count} files.")

    @classmethod
    def search_files(cls, query: str):
        if not cls.ix:
            raise Exception("Index not initialized.")

        with cls.ix.searcher() as searcher:
            parser = MultifieldParser(["file", "file_name"], schema=cls.schema)
            parsed_query = parser.parse(query)
            results = searcher.search(parsed_query)

            return [result["file"] for result in results]

    @classmethod
    def get_nbr_indexed_files(cls):
        if not cls.ix:
            raise Exception("Index not initialized.")

        with cls.ix.searcher() as searcher:
            return searcher.doc_count_all()
