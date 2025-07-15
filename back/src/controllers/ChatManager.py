import json
import logging
import queue
import time
from datetime import datetime

from db import ChatMessage, ChatSession, get_db
from fastapi import HTTPException
from utils import read_content


class ChatManager:
    queue = queue.Queue()
    running_chat = None

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
            f"{msg['user']}: {msg['content']}" for msg in messages
        ]

        prompt = (
            "You are given a conversation and some files provided by the user. "
            "Use the file contents if relevant to answer the user's latest question.\n\n"
            + "\n".join(file_texts)
            + "\n\n--- Conversation ---\n"
            + "\n".join(chat_texts)
        )

        return prompt, files

    @classmethod
    def loop(cls):
        time.sleep(10)
        while True:
            chat_id = cls.queue.get()
            cls.running_chat = chat_id
            logging.info(f"CHAT >> Processing chat session: {chat_id}")

            # Simulate processing time
            # After processing, reset running chat
            time.sleep(10)
            prompt, files = cls.generate_prompt(chat_id)
            logging.critical(prompt)
            chat_name = "ChatGPT"
            chat_answer = "Maybe one day I will be able to answer this question."

            db = get_db()
            try:
                db.add(
                    ChatMessage(
                        session_id=chat_id,
                        user=chat_name,
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

    @classmethod
    def add_to_queue(cls, chat_id):
        cls.queue.put(chat_id)

    @classmethod
    def is_running(cls, chat_id):
        return cls.running_chat == chat_id or chat_id in cls.queue.queue

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
    def add_message(cls, session_id: str, content: str, files: list = None):
        if not cls.is_running(session_id):
            db = get_db()
            try:
                new_message = ChatMessage(
                    session_id=session_id,
                    user="user",
                    content=content,
                    files=files if files else None,
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
