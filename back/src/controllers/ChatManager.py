import json
import logging
import queue
import time
from datetime import datetime
from typing import List

from db import ChatMessage, ChatSession, get_db
from fastapi import HTTPException
from tools.ai import request_llm
from utils import read_content


class ChatManager:
    queue = queue.Queue()
    running_chat = None
    running_answer = ""

    def start_thread():
        ChatManager.loop()

    @classmethod
    def generate_prompt(cls, chat_id):
        messages = cls.get_chat_messages(chat_id)
        if not messages:
            return "No context available.", []

        files = json.loads(messages[-1]["files"])
        file_texts = [
            f"--- File: {file} ---\n{read_content(file) or '[File could not be read]'}"
            for file in files
        ]

        chat_texts = [
            f"""
--- Message ---
User: {msg['user']}
Date: {msg['date'].strftime('%Y-%m-%d %H:%M:%S')}
Files: {', '.join(json.loads(msg['files'])) if msg['files'] else 'None'}
Message: {msg['content']}
"""
            for msg in messages
        ]

        prompt = (
            "You are given a conversation and some files provided by the user.\n"
            "You are an AI Chat BOT that can answer questions based on the conversation and files.\n"
            "Use the file contents if relevant to ANSWER the user's LATEST prompt.\n\n"
            + "\n".join(file_texts)
            + "\n\n--- Conversation ---\n"
            + "\n".join(chat_texts)
        )

        return prompt, files

    @classmethod
    def stream_callback(cls, data):
        if cls.running_answer is not None:
            cls.running_answer += data
        else:
            cls.running_answer = data

    @classmethod
    def loop(cls):
        time.sleep(10)
        while True:
            chat_id = cls.queue.get()
            cls.running_chat = chat_id
            cls.running_answer = ""
            logging.critical(f"CHAT >> Processing chat session: {chat_id}")

            # Simulate processing time
            # After processing, reset running chat
            prompt, files = cls.generate_prompt(chat_id)
            try:
                ai_type, model, chat_answer = request_llm(
                    "chat", prompt, stream_callback=cls.stream_callback
                )
            except Exception as e:
                ai_type = "Error"
                model = ""
                chat_answer = f"Error: {e}"

            db = get_db()
            try:
                db.add(
                    ChatMessage(
                        session_id=chat_id,
                        user=f"{ai_type} - {model}",
                        content=chat_answer,
                        files=json.dumps(files) if files else None,
                        date=datetime.now(),
                    )
                )
                db.commit()
            except Exception as e:
                logging.error(
                    f"CHAT >> Error processing chat session {chat_id}: {str(e)}"
                )
            finally:
                db.close()
                cls.running_chat = None
                cls.running_answer = ""

    @classmethod
    def add_to_queue(cls, chat_id):
        cls.queue.put(chat_id)

    @classmethod
    def is_running(cls, chat_id):
        if cls.running_chat == chat_id:
            return {
                "state": "running",
                "answer": cls.running_answer,
            }
        elif chat_id in cls.queue.queue:
            return {
                "state": "queued",
            }
        else:
            return {
                "state": "not_running",
            }

    @classmethod
    def list_chats(cls):
        db = get_db()
        try:
            sessions = [s.__dict__ for s in db.query(ChatSession).all()]
            sessions.sort(key=lambda x: x["date"], reverse=True)
            return sessions
        except Exception as e:
            logging.error(f"Error listing chat sessions: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        finally:
            db.close()

    @classmethod
    def create_chat(cls, title: str):
        db = get_db()
        try:
            new_session = ChatSession(title=title, date=datetime.now())
            db.add(new_session)
            db.commit()
            return {"id": new_session.id, "title": new_session.title}
        except Exception as e:
            logging.error(f"Error creating chat session: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        finally:
            db.close()

    @classmethod
    def edit_chat(cls, session_id: str, title: str, description: str):
        db = get_db()
        try:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not session:
                raise HTTPException(status_code=404, detail="Chat session not found")
            session.title = title
            session.description = description
            db.commit()
            return {"id": session.id, "title": session.title}
        except Exception as e:
            logging.error(f"Error editing chat session: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        finally:
            db.close()

    @classmethod
    def get_chat_info(cls, session_id: str):
        db = get_db()
        try:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not session:
                raise HTTPException(status_code=404, detail="Chat session not found")
            return session.__dict__
        except Exception as e:
            logging.error(f"Error retrieving chat info: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        finally:
            db.close()

    @classmethod
    def get_chat_messages(cls, session_id: str):
        db = get_db()
        try:
            messages = [
                m.__dict__
                for m in (
                    db.query(ChatMessage)
                    .filter(ChatMessage.session_id == session_id)
                    .all()
                )
            ]
            messages.sort(key=lambda x: x["date"])
            return messages
        except Exception as e:
            logging.error(f"Error retrieving chat messages: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
        finally:
            db.close()

    @classmethod
    def add_message(cls, session_id: str, content: str, files: List[str] = None):
        if cls.is_running(session_id).get("state") == "not_running":
            db = get_db()
            try:
                new_message = ChatMessage(
                    session_id=session_id,
                    user="user",
                    content=content,
                    files=json.dumps(files) if files else None,
                    date=datetime.now(),
                )
                db.add(new_message)
                db.commit()
                db.refresh(new_message)
                cls.add_to_queue(session_id)
                return new_message.__dict__
            except Exception as e:
                logging.error(f"Error adding chat message: {str(e)}")
                raise HTTPException(status_code=500, detail="Internal Server Error")
            finally:
                db.close()
        else:
            raise HTTPException(
                status_code=400, detail="Chat session is currently running"
            )
