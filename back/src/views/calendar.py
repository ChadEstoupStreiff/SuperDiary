import datetime
import logging
import traceback

from db import CalendarRecord, get_db
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/calendar", tags=["Calendar"])


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
            start_time=datetime.datetime.strptime(start_time, "%H:%M:%S")
            if start_time
            else None,
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


@router.put("/record/{record_id}")
async def edit_calendar_record(
    record_id: str,
    title: str = None,
    project: str = None,
    time_spent: float = None,
    description: str = None,
    location: str = None,
    attendees: str = None,
):
    """
    Edit an existing calendar record.
    """
    db = get_db()
    try:
        record = db.query(CalendarRecord).filter(CalendarRecord.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")

        if title is not None:
            record.title = title
        if project is not None:
            record.project = project
        if time_spent is not None:
            record.time_spent = time_spent
        if description is not None:
            record.description = description
        if location is not None:
            record.location = location
        if attendees is not None:
            record.attendees = attendees

        db.commit()
        return {"message": "Record updated successfully"}
    except Exception as e:
        db.rollback()
        logging.error(f"Error editing calendar record {record_id}: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Error editing calendar record: {str(e)}"
        )
    finally:
        db.close()


@router.delete("/record/{record_id}")
async def delete_calendar_record(record_id: str):
    """
    Delete a calendar record by its ID.
    """
    db = get_db()
    try:
        record = db.query(CalendarRecord).filter(CalendarRecord.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")

        db.delete(record)
        db.commit()
        return {"message": "Record deleted successfully"}
    except Exception as e:
        db.rollback()
        logging.error(f"Error deleting calendar record {record_id}: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Error deleting calendar record: {str(e)}"
        )
    finally:
        db.close()


@router.get("/search")
async def search_calendar_records(
    query: str = None, start_date: str = None, end_date: str = None, project: str = None
):
    """
    Search for calendar records based on query, start date, end date, and optional project.
    """
    db = get_db()
    try:
        db_query = db.query(CalendarRecord)
        if query:
            db_query = db_query.filter(CalendarRecord.title.ilike(f"%{query}%"))
        if start_date:
            db_query = db_query.filter(CalendarRecord.date >= start_date)
        if end_date:
            db_query = db_query.filter(CalendarRecord.date <= end_date)
        if project:
            db_query = db_query.filter(CalendarRecord.project == project)

        records = db_query.all()
        records = [r.__dict__ for r in records]
        records.sort(key=lambda x: x["date"], reverse=True)
        return records
    except Exception as e:
        logging.error(f"Error searching calendar records: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Error searching calendar records: {str(e)}"
        )
    finally:
        db.close()