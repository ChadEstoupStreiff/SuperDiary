from enum import Enum

from sqlalchemy import TEXT, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import declarative_base, mapped_column

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


class Tag(Base):
    __tablename__ = "Tag"

    name = Column(String(64), primary_key=True, index=True)
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

    name = Column(String(256), primary_key=True, nullable=False)
    description = Column(TEXT(16320), nullable=True)
    color = Column(String(32), nullable=False)


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

    id = Column(String(64), primary_key=True, index=True)
    project = mapped_column(
        ForeignKey("Project.name", ondelete="CASCADE", onupdate="CASCADE")
    )
    title = Column(String(256), nullable=False)
    description = Column(TEXT(16320), nullable=True)
    time_worked = Column(Integer, nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    location = Column(String(256), nullable=True)
    attendees = Column(TEXT(16320), nullable=True)
