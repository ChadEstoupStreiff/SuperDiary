import logging
import mimetypes
import os
import traceback
from datetime import datetime
from typing import List

from controllers import FileManager, OCRManager, TranscriptionManager
from fastapi import APIRouter, HTTPException, UploadFile
from starlette.responses import FileResponse

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload")
async def upload_files(files: List[UploadFile], subdirectory: str, date: str = None):
    """
    Upload a file to the system.
    """
    try:
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        file_directory = os.path.join("/shared", date, subdirectory)
        if not os.path.exists(file_directory):
            os.makedirs(file_directory, exist_ok=True)

        for file in files:
            file_path = os.path.join(file_directory, file.filename)
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)

            file_extension = os.path.splitext(file.filename)[1].lower().replace(".", "")
            if (
                file_extension == "png"
                or file_extension == "jpg"
                or file_extension == "jpeg"
                or file_extension == "bmp"
                or file_extension == "webp"
            ):
                OCRManager.add_file_to_queue(file_path)
            elif file_extension == "mp3" or file_extension == "wav":
                TranscriptionManager.add_file_to_queue(file_path)
                
        return {"message": f"{len(files)} files uploaded successfully."}
    except Exception as e:
        logging.error(f"Error uploading files: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error uploading files: {str(e)}")


@router.delete("/delete/{file:path}")
async def delete_file(file: str):
    """
    Delete a file from the system.
    """
    try:
        file_path = os.path.join(file)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file} does not exist.")

        os.remove(file_path)
        return {"message": f"File {file} deleted successfully."}
    except FileNotFoundError as e:
        logging.error(f"File not found: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/download/{file:path}")
async def get_file(file: str):
    """
    Get a file by its path. Returns correct media type for browser rendering.
    """
    if os.path.exists(file):
        media_type, _ = mimetypes.guess_type(file)
        return FileResponse(
            file,
            media_type=media_type or "application/octet-stream",
            filename=os.path.basename(file),
        )
    else:
        raise HTTPException(status_code=404, detail=f"File {file} not found.")


def walk_files():
    return [
        os.path.join(dp, filename)
        for dp, _, filenames in os.walk("/shared")
        for filename in filenames
    ]


@router.get("/list")
async def list_files():
    """
    List all files in the system.
    """
    return walk_files()


@router.get("/count")
async def count_files():
    """
    Count the number of files in the system.
    """
    return len(walk_files())


@router.get("/search")
async def search_files(query: str):
    """
    Search for files based on a query.
    """
    try:
        return FileManager.search_files(query)
    except Exception as e:
        logging.error(f"Error searching files: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error searching files: {str(e)}")
