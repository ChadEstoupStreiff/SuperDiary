from typing import Optional

from controllers.LinkManager import LinkManager
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/links", tags=["Link"])


@router.get("/list/{file:path}")
def list_links(file: str):
    return LinkManager.list_links(file)

@router.post("/add")
def add_link(
    fileA: str,
    fileB: str,
    force: Optional[float] = 1.0,
    comment: Optional[str] = None,
):
    LinkManager.add_link(fileA, fileB, force, comment)
    return {"status": "success"}

@router.delete("/remove")
def remove_link(fileA: str, fileB: str):
    LinkManager.remove_link(fileA, fileB)
    return {"status": "success"}
