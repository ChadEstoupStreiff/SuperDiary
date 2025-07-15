import uuid
from enum import Enum

from sqlalchemy import TEXT, Column, DateTime, Float, ForeignKey, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import declarative_base, mapped_column

Base = declarative_base()

class StockPile(Base):
    __tablename__ = "StockPile"

    key = Column(String(64), primary_key=True, index=True)
    value = Column(String(512), nullable=False)

class Setting(Base):
    __tablename__ = "Setting"

    key = Column(String(64), primary_key=True, index=True)
    value = Column(TEXT(130560), nullable=False)


class Note(Base):
    __tablename__ = "Note"

    file = Column(String(512), primary_key=True, index=True)
    date = Column(DateTime, nullable=False)
    note = Column(TEXT(130560), nullable=False)


class TaskStateEnum(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class OCR(Base):
    __tablename__ = "OCR"

    file = Column(String(512), primary_key=True, index=True)
    date = Column(DateTime, nullable=False)
    ocr = Column(TEXT(130560), nullable=False)
    blip = Column(TEXT(130560), nullable=True)


class OCRTask(Base):
    __tablename__ = "OCRTask"

    file = Column(String(512), primary_key=True, index=True)
    state = Column(
        SQLEnum(TaskStateEnum), nullable=False, default=TaskStateEnum.PENDING
    )
    added = Column(DateTime, primary_key=True)
    completed = Column(DateTime, nullable=True)
    result = Column(TEXT(130560), nullable=True)


class Summary(Base):
    __tablename__ = "Summary"

    file = Column(String(512), primary_key=True, index=True)
    date = Column(DateTime, nullable=False)
    summary = Column(TEXT(130560), nullable=False)
    keywords = Column(TEXT(130560), nullable=False)


class SummaryTask(Base):
    __tablename__ = "SummaryTask"

    file = Column(String(512), primary_key=True, index=True)
    state = Column(
        SQLEnum(TaskStateEnum), nullable=False, default=TaskStateEnum.PENDING
    )
    added = Column(DateTime, primary_key=True)
    completed = Column(DateTime, nullable=True)
    result = Column(TEXT(130560), nullable=True)


class Transcription(Base):
    __tablename__ = "Transcription"

    file = Column(String(512), primary_key=True, index=True)
    date = Column(DateTime, nullable=False)
    transcription = Column(TEXT(130560), nullable=False)


class TranscriptionTask(Base):
    __tablename__ = "TranscriptionTask"

    file = Column(String(512), primary_key=True, index=True)
    state = Column(
        SQLEnum(TaskStateEnum), nullable=False, default=TaskStateEnum.PENDING
    )
    added = Column(DateTime, primary_key=True)
    completed = Column(DateTime, nullable=True)
    result = Column(TEXT(130560), nullable=True)


class Tag(Base):
    __tablename__ = "Tag"

    name = Column(String(20), primary_key=True, index=True)
    color = Column(String(32), nullable=False)


class TagFile(Base):
    __tablename__ = "TagFile"

    file = Column(String(512), primary_key=True, index=True)
    tag = mapped_column(
        ForeignKey("Tag.name", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        index=True,
    )


class Project(Base):
    __tablename__ = "Project"

    name = Column(String(50), primary_key=True, nullable=False)
    description = Column(TEXT(130560), nullable=True)
    color = Column(String(32), nullable=False)
    notes = Column(TEXT(130560), default="")
    todo = Column(TEXT(130560), default="[]")


class ProjectFile(Base):
    __tablename__ = "ProjectFile"

    project = mapped_column(
        ForeignKey("Project.name", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        index=True,
    )
    file = Column(String(512), primary_key=True, index=True)


class CalendarRecord(Base):
    __tablename__ = "CalendarRecord"

    id = Column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    project = mapped_column(
        ForeignKey("Project.name", ondelete="CASCADE", onupdate="CASCADE")
    )
    date = Column(DateTime, nullable=False)
    start_time = Column(DateTime, nullable=True)
    time_spent = Column(Float, nullable=False)
    title = Column(String(512), nullable=False)
    description = Column(TEXT(130560), nullable=True)
    location = Column(String(512), nullable=True)
    attendees = Column(TEXT(130560), nullable=True)


class ChatSession(Base):
    __tablename__ = "ChatSession"

    id = Column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    title = Column(String(512), nullable=False)
    description = Column(TEXT(130560), nullable=True)
    date = Column(DateTime, nullable=False)

class ChatMessage(Base):
    __tablename__ = "ChatMessage"

    id = Column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    session_id = mapped_column(
        ForeignKey("ChatSession.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    date = Column(DateTime, nullable=False)
    user = Column(String(32), nullable=False)  # e.g., 'user', 'assistant'

    files = Column(TEXT(130560), nullable=True)
    content = Column(TEXT(130560), nullable=False)