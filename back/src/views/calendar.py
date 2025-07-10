import logging
import traceback

from db import CalendarRecord, get_db
from fastapi import APIRouter, HTTPException
import datetime
router = APIRouter(prefix="/calendar", tags=["Calendar"])


@router.get("/records")
async def get_calendar(project: str = None, date: str = None):
    """
    Get calendar records for a specific project and date.
    """
    db = get_db()
    try:
        query = db.query(CalendarRecord)
        if project:
            query = query.filter(CalendarRecord.project == project)
        if date:
            query = query.filter(CalendarRecord.date == date)
        records = query.all()
        records = [record.__dict__ for record in records]
        records.sort(key=lambda x: x["date"], reverse=True)
        return records
    except Exception as e:
        logging.error(f"Error retrieving calendar records: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Error retrieving calendar records: {str(e)}"
        )
    finally:
        db.close()


@router.get("/record/{record_id}")
async def get_calendar_record(record_id: int):
    """
    Get a specific calendar record by its ID.
    """
    db = get_db()
    try:
        record = db.query(CalendarRecord).filter(CalendarRecord.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        return record.to_dict()
    except Exception as e:
        logging.error(f"Error retrieving calendar record {record_id}: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Error retrieving calendar record: {str(e)}"
        )
    finally:
        db.close()


@router.post("/record")
async def create_calendar_record(
    project: str,
    date: str,
    time_spent: float,
    title: str,
    start_time: str = None,
    description: str = None,
    location: str = None,
    attendees: str = None,
):
    """
    Create a new calendar record.
    """
    db = get_db()
    try:
        record = CalendarRecord(
            project=project,
            date=date,
            start_time=datetime.datetime.strptime(start_time, "%H:%M:%S") if start_time else None,
            time_spent=time_spent,
            title=title,
            description=description,
            location=location,
            attendees=attendees,
        )
        db.add(record)
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error(f"Error creating calendar record: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Error creating calendar record: {str(e)}"
        )
    finally:
        db.close()
