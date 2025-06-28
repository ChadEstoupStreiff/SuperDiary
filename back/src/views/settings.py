import logging
import traceback

from db import Setting, get_db
from fastapi import APIRouter, HTTPException
from typing import Any
import json

router = APIRouter(tags=["Settings"])

default_settings = {
    "enable_auto_ocr": True,
    "enable_auto_transcription": True,
    "enable_auto_summary": True,
    "transcription_type": "llama",
    "transcription_model": "small",
    "summarization_type": "llama",
    # "summarization_model": "llama3.2:3b",
    # "summarization_model": "llama3.1:8b",
    "summarization_model": "llama3.2:1b",
}

def format_value(value: Any) -> str:
    """
    Format the value based on its type.
    """
    if isinstance(value, bool):
        return f"bool:{str(value).lower()}"
    elif isinstance(value, int):
        return f"int:{value}"
    elif isinstance(value, str):
        return f"str:{value.strip()}"
    return f"json:{json.dumps(value)}"  # Default to JSON format for other types

def parse_value(value: str) -> Any:
    """
    Parse the value from the database to its appropriate type.
    """
    if value.startswith("bool:"):
        return value[5:].lower() in ("true", "1", "yes")
    elif value.startswith("int:"):
        return int(value[4:])
    elif value.startswith("str:"):
        return value[4:].strip()
    return json.loads(value[5:])  # Default to JSON parsing for other types

def get_setting(key: str, default=None):
    """
    Get a setting value by key, returning the default if not found.
    """
    db = get_db()
    try:
        setting = db.query(Setting).filter(Setting.key == key).first()
        return parse_value(setting.value) if setting else default_settings.get(key, default)
    except Exception as e:
        logging.error(f"Error retrieving setting {key}: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Error retrieving setting {key}: {str(e)}"
        )
    finally:
        db.close()


@router.get("/settings/{key}")
async def get_setting_value(key: str):
    """
    Get a specific setting value by key.
    """
    try:
        value = get_setting(key)
        if value is None:
            raise HTTPException(status_code=404, detail=f"Setting {key} not found.")
        return {key: value}
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Error retrieving setting {key}: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Error retrieving setting {key}: {str(e)}"
        )


@router.get("/settings")
async def get_settings():
    """
    Get the current settings.
    """
    db = get_db()
    try:
        result = {setting.key: parse_value(setting.value) for setting in db.query(Setting).all()}
        for key, value in default_settings.items():
            if key not in result:
                result[key] = value
        return result
    except Exception as e:
        logging.error(f"Error retrieving settings: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Error retrieving settings: {str(e)}"
        )
    finally:
        db.close()


@router.post("/settings")
async def set_settings(settings: dict):
    """
    Set the current settings.
    """
    db = get_db()
    try:
        for key, value in settings.items():
            
            setting = db.query(Setting).filter(Setting.key == key).first()
            if setting:
                setting.value = format_value(value)
            else:
                new_setting = Setting(key=key, value=format_value(value))
                db.add(new_setting)
        db.commit()
        return {"message": "Settings updated successfully."}
    except Exception as e:
        db.rollback()
        logging.error(f"Error updating settings: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Error updating settings: {str(e)}"
        )
    finally:
        db.close()
