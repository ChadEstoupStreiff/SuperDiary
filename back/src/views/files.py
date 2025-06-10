import logging
import mimetypes
import os
import traceback
from datetime import datetime
from typing import List

from controllers import NoteManager, FileManager, OCRManager, SummarizeManager, TranscriptionManager
from fastapi import APIRouter, HTTPException, UploadFile
from starlette.responses import FileResponse
from views.settings import get_setting

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload")
async def upload_files(
    files: List[UploadFile], subdirectory: str, date: datetime = None
):
    """
    Upload a file to the system.
    """
    try:
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        else:
            date = date.strftime("%Y-%m-%d")

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
            ) and get_setting("enable_auto_ocr"):
                OCRManager.add_file_to_queue(file_path)
            elif (
                file_extension == "mp3"
                or file_extension == "wav"
                or file_extension == "mp4"
                or file_extension == "avi"
                or file_extension == "mov"
            ) and get_setting("enable_auto_transcription"):
                TranscriptionManager.add_file_to_queue(file_path)
            if get_setting("enable_auto_summary"):
                SummarizeManager.add_file_to_queue(file_path)

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

        SummarizeManager.delete(file_path)
        OCRManager.delete(file_path)
        TranscriptionManager.delete(file_path)
        NoteManager.delete(file_path)

        os.remove(file_path)
        return {"message": f"File {file} deleted successfully."}
    except FileNotFoundError as e:
        logging.error(f"File not found: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/move/{file:path}")
async def move_file(
    file: str, subfolder: str, date: datetime = None, new_name: str = None
):
    """
    Move a file to a new location.
    """

    try:
        file_path = os.path.join(file)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file} does not exist.")

        if new_name is None:
            new_name = os.path.basename(file)
        if date is None:
            date = file.split("/")[1]
        else:
            date = date.strftime("%Y-%m-%d")
        if subfolder is None:
            subfolder = file.split("/")[2]

        new_directory = os.path.join("/shared", date, subfolder)
        if not os.path.exists(new_directory):
            os.makedirs(new_directory, exist_ok=True)

        new_file_path = os.path.join(new_directory, new_name)
        if os.path.exists(new_file_path):
            raise HTTPException(
                status_code=400,
                detail=f"File {new_name} already exists in {new_directory}.",
            )

        SummarizeManager.move(file_path, new_file_path)
        OCRManager.move(file_path, new_file_path)
        TranscriptionManager.move(file_path, new_file_path)
        NoteManager.move(file_path, new_file_path)
        os.rename(file_path, new_file_path)

        return {"message": f"File {file} moved to {new_file_path} successfully."}
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
        # media_type, _ = mimetypes.guess_type(file)
        return FileResponse(
            file,
            media_type="application/octet-stream",
            filename=os.path.basename(file),
        )
    else:
        raise HTTPException(status_code=404, detail=f"File {file} not found.")


@router.get("/metadata/{file:path}")
async def get_file_metadata(file: str):
    """
    Get metadata of a file.
    """
    try:
        file_path = os.path.join(file)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file} does not exist.")

        metadata = {
            "size": os.path.getsize(file_path),
            "created": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
            "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
            "path": file_path,
            "mime_type": mimetypes.guess_type(file_path)[0]
            or "application/octet-stream",
        }
        return metadata
    except FileNotFoundError as e:
        logging.error(f"File not found: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=404, detail=str(e))


def walk_files():
    return [
        os.path.join(dp, filename)
        for dp, _, filenames in os.walk("/shared")
        for filename in filenames
        if filename != ".DS_Store"
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
