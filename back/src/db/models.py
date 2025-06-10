from enum import Enum

from sqlalchemy import TEXT, Column, DateTime, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Setting(Base):
    __tablename__ = "Setting"

    key = Column(String(64), primary_key=True, index=True)
    value = Column(TEXT(16320), nullable=False)

class Note(Base):
    __tablename__ = "Note"

    file = Column(String(512), primary_key=True, index=True)
    date = Column(DateTime, nullable=False)
    note = Column(TEXT(16320), nullable=False)

class TaskStateEnum(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class OCR(Base):
    __tablename__ = "OCR"

    file = Column(String(512), primary_key=True, index=True)
    date = Column(DateTime, nullable=False)
    ocr = Column(TEXT(16320), nullable=False)


class OCRTask(Base):
    __tablename__ = "OCRTask"

    file = Column(String(512), primary_key=True, index=True)
    state = Column(
        SQLEnum(TaskStateEnum), nullable=False, default=TaskStateEnum.PENDING
    )
    added = Column(DateTime, primary_key=True)
    completed = Column(DateTime, nullable=True)
    result = Column(TEXT(16320), nullable=True)


class Summary(Base):
    __tablename__ = "Summary"

    file = Column(String(512), primary_key=True, index=True)
    date = Column(DateTime, nullable=False)
    summary = Column(TEXT(16320), nullable=False)
    keywords = Column(TEXT(16320), nullable=False)


class SummaryTask(Base):
    __tablename__ = "SummaryTask"

    file = Column(String(512), primary_key=True, index=True)
    state = Column(
        SQLEnum(TaskStateEnum), nullable=False, default=TaskStateEnum.PENDING
    )
    added = Column(DateTime, primary_key=True)
    completed = Column(DateTime, nullable=True)
    result = Column(TEXT(16320), nullable=True)


class Transcription(Base):
    __tablename__ = "Transcription"

    file = Column(String(512), primary_key=True, index=True)
    date = Column(DateTime, nullable=False)
    transcription = Column(TEXT(16320), nullable=False)


class TranscriptionTask(Base):
    __tablename__ = "TranscriptionTask"

    file = Column(String(512), primary_key=True, index=True)
    state = Column(
        SQLEnum(TaskStateEnum), nullable=False, default=TaskStateEnum.PENDING
    )
    added = Column(DateTime, primary_key=True)
    completed = Column(DateTime, nullable=True)
    result = Column(TEXT(16320), nullable=True)
