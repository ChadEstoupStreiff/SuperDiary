from datetime import datetime

from db import Note, get_db


class NoteManager:
    @classmethod
    def get(cls, file):
        """
        Get the note for a file.
        """
        db = get_db()
        note = db.query(Note).filter(Note.file == file).first()
        db.close()
        if not note:
            raise Exception("Note not found for this file.")
        return {
            "file": note.file,
            "date": note.date,
            "note": note.note,
        }

    @classmethod
    def set(cls, file, note):
        """
        Set the note for a file.
        """
        db = get_db()
        try:
            existing_note = db.query(Note).filter(Note.file == file).first()
            if existing_note:
                existing_note.note = note
                existing_note.date = datetime.now()
            else:
                new_note = Note(file=file, note=note)
                db.add(new_note)
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
