from controllers.ChatManager import ChatManager
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional


router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/list")
def list_chat_sessions():
    return ChatManager.list_chats()


@router.get("/{session_id}/is_running")
def is_chat_running(session_id: str):
    return ChatManager.is_running(session_id)


@router.post("/create")
def create_chat_session(title: str):
    return ChatManager.create_chat(title)


@router.put("/{session_id}/edit")
def edit_chat_session(session_id: str, title: str, description: str):
    return ChatManager.edit_chat(session_id, title, description)


@router.get("/{session_id}/info")
def get_chat_info(session_id: str):
    return ChatManager.get_chat_info(session_id)


@router.get("/{session_id}/messages")
def get_chat_messages(session_id: str):
    return ChatManager.get_chat_messages(session_id)

class ChatMessageRequest(BaseModel):
    content: str
    files: Optional[List[str]] = None

@router.post("/{session_id}/message")
def add_chat_message(session_id: str, request: ChatMessageRequest):
    return ChatManager.add_message(session_id, request.content, request.files)