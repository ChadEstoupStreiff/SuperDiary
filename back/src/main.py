import logging

import uvicorn

from fastapi import FastAPI
from controllers import FileManager, OCRManager
from threading import Thread
from db import DB
from db.models import Base

app = FastAPI()


import views.files

app.include_router(views.files.router)

import views.ocr
app.include_router(views.ocr.router)



if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    Base.metadata.create_all(bind=DB().engine)

    FileManager.setup()

    ocr_thread = Thread(target=OCRManager.start_thread)
    ocr_thread.daemon = True  # Daemonize thread
    ocr_thread.start()

    uvicorn.run(app, host="0.0.0.0", port=80)
    ocr_thread.join()  # Wait for the OCR thread to finish
