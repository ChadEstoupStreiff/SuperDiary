import json
import logging
import os
import traceback
from datetime import datetime
from io import BytesIO
from typing import List

from controllers.FileManager import FileManager
from controllers.NoteManager import NoteManager
from controllers.OCRManager import OCRManager
from controllers.SummarizeManager import SummarizeManager
from controllers.TranscriptionManager import TranscriptionManager
from db import get_db
from db.models import ProjectFile, TagFile
from fastapi import APIRouter, HTTPException, UploadFile
from PIL import Image
from pillow_heif import register_heif_opener
from starlette.responses import FileResponse
from utils import guess_mime
from views.settings import get_setting
from views.stockpile import StockPile, get_recent_added

router = APIRouter(prefix="/files", tags=["Files"])

register_heif_opener()


def add_recent_added_file(file: str):
    try:
        recent_added_files = get_recent_added()
    except HTTPException:
        recent_added_files = []

    if file in recent_added_files:
        recent_added_files.remove(file)
    if len(recent_added_files) >= 10:
        recent_added_files.pop()
    recent_added_files.insert(0, file)

    db = get_db()
    try:
        stockpile_item = (
            db.query(StockPile).filter(StockPile.key == "recentadded").first()
        )
        if stockpile_item:
            stockpile_item.value = json.dumps(recent_added_files)
        else:
            stockpile_item = StockPile(
                key="recentadded", value=json.dumps(recent_added_files)
            )
            db.add(stockpile_item)
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error(f"Error adding recent added file {file}: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Error adding recent added file: {str(e)}"
        )
    finally:
        db.close()


@router.post("/upload")
async def upload_files(
    files: List[UploadFile],
    subdirectory: str,
    date: str = None,
    file_edit_info: str = None,
):
    """
    Upload a file to the system.
    """
    file_edit_info = json.loads(file_edit_info) if file_edit_info else {}
    date = date or datetime.now().strftime("%Y-%m-%d")
    try:
        for file in files:
            file_date = file_edit_info.get(file.filename, {}).get("date", date)
            file_name = (
                file_edit_info.get(file.filename, {})
                .get("name", file.filename)
                .replace("/", "_")
                .replace("\\", "_")
                .replace(":", "-")
                .replace("?", "")
            )

            os.makedirs(os.path.join("/shared", file_date, subdirectory), exist_ok=True)
            file_ext = os.path.splitext(file.filename)[1].lower()

            file_path = (
                os.path.join(
                    "/shared",
                    file_date,
                    subdirectory,
                    os.path.splitext(file_name)[0] + ".png",
                )
                if file_ext == ".heic"
                else os.path.join("/shared", file_date, subdirectory, file_name)
            )
            file_exists = os.path.exists(file_path)

            if file_ext == ".heic":
                content = await file.read()
                image = Image.open(BytesIO(content))
                image.save(file_path, format="PNG")
            else:
                with open(file_path, "wb") as f:
                    f.write(await file.read())

            add_recent_added_file(file_path)

            if file_exists:
                os.utime(file_path, None)
            else:
                auto_summary = get_setting("enable_auto_summary")
                mime = guess_mime(file_path)

                if (
                    mime
                    and mime.startswith("image/")
                    and get_setting("enable_auto_ocr")
                ):
                    OCRManager.add_file_to_queue(file_path)
                    if auto_summary:
                        SummarizeManager.add_file_to_queue(file_path)

                elif (
                    mime and (mime.startswith("audio/") or mime.startswith("video/"))
                ) and get_setting("enable_auto_transcription"):
                    TranscriptionManager.add_file_to_queue(file_path)
                    if auto_summary:
                        SummarizeManager.add_file_to_queue(file_path)

                elif auto_summary:
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
    file: str, subfolder: str = None, date: str = None, name: str = None
):
    """
    Move a file to a new location.
    """
    file = file.strip()

    try:
        if not os.path.exists(file):
            raise FileNotFoundError(f"File {file} does not exist.")

        if name is None:
            name = os.path.basename(file)
        if date is None:
            date = file.split("/")[2]
        if subfolder is None:
            subfolder = file.split("/")[3]

        new_directory = os.path.join("/shared", date, subfolder)
        if not os.path.exists(new_directory):
            os.makedirs(new_directory, exist_ok=True)

        new_file_path = os.path.join(new_directory, name)
        if os.path.exists(new_file_path):
            raise HTTPException(
                status_code=400,
                detail=f"File {name} already exists in {new_directory}.",
            )

        SummarizeManager.move(file, new_file_path)
        OCRManager.move(file, new_file_path)
        TranscriptionManager.move(file, new_file_path)
        NoteManager.move(file, new_file_path)
        db = get_db()
        try:
            # Update ProjectFile entries
            project_files = db.query(ProjectFile).filter(ProjectFile.file == file).all()
            for project_file in project_files:
                project_file.file = new_file_path
            db.commit()

            # Update TagFile entries
            tag_files = db.query(TagFile).filter(TagFile.file == file).all()
            for tag_file in tag_files:
                tag_file.file = new_file_path
            db.commit()
        except Exception as e:
            db.rollback()
            logging.error(f"Error updating database entries: {str(e)}")
            logging.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"Error updating database entries: {str(e)}"
            )
        finally:
            db.close()
        os.rename(file, new_file_path)

        return new_file_path
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
        return FileResponse(
            file,
            media_type=guess_mime(file),
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
            "mime_type": guess_mime(file_path),
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
    result = walk_files()
    result.sort()
    result.reverse()
    return result


@router.get("/count")
async def count_files():
    """
    Count the number of files in the system.
    """
    return len(walk_files())


@router.get("/search")
async def search_files(
    text: str = None,
    start_date: str = None,
    end_date: str = None,
    subfolder: str = None,
    types: str = None,
    projects: str = None,
    tags: str = None,
    search_mode: int = 0, # 0: FAST, 1: NORMAL, 2: DEEP
):
    """
    Search for files based on a query.
    """
    if text is not None and len(text) == 0:
        text = None
    if types is not None and len(types) == 0:
        types = None
    if subfolder is not None and len(subfolder) == 0:
        subfolder = None
    if projects is not None and len(projects) == 0:
        projects = None
    if tags is not None and len(tags) == 0:
        tags = None

    try:
        result = FileManager.search_files(
            text,
            start_date,
            end_date,
            subfolder.split(",") if subfolder else None,
            types.split(",") if types else None,
            projects.split(",") if projects else None,
            tags.split(",") if tags else None,
            search_mode=search_mode,
        )
        result.sort()
        result.reverse()
        return result
    except Exception as e:
        logging.error(f"Error searching files: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error searching files: {str(e)}")


@router.get("/index")
async def index_files():
    """
    Index all files in the system.
    """
    try:
        return FileManager.get_indexed_files()
    except Exception as e:
        logging.error(f"Error getting indexed files: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Error getting indexed files: {str(e)}"
        )


@router.post("/index")
async def reindex_files():
    """
    Reindex all files in the system.
    """
    try:
        FileManager.index_files()
        return {"message": "Files reindexed successfully."}
    except Exception as e:
        logging.error(f"Error reindexing files: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error reindexing files: {str(e)}")
