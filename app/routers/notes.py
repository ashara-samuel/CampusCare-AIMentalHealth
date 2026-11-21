"""Per-user notes. Every query is scoped to the authenticated user, so one user
can never read, edit, or delete another's notes (no IDOR)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import Note, User
from ..schemas import NoteIn, NoteOut

router = APIRouter(prefix="/notes", tags=["notes"])


def _own_note(db: Session, note_id: int, user: User) -> Note:
    note = db.scalar(select(Note).where(Note.id == note_id, Note.user_id == user.id))
    if note is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Note not found")
    return note


@router.get("", response_model=list[NoteOut])
def list_notes(db: Session = Depends(get_db),
               user: User = Depends(get_current_user)) -> list[Note]:
    return list(db.scalars(
        select(Note).where(Note.user_id == user.id).order_by(Note.updated_at.desc())))


@router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(body: NoteIn, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)) -> Note:
    note = Note(user_id=user.id, title=body.title, text=body.text)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("/{note_id}", response_model=NoteOut)
def get_note(note_id: int, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)) -> Note:
    return _own_note(db, note_id, user)


@router.put("/{note_id}", response_model=NoteOut)
def update_note(note_id: int, body: NoteIn, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)) -> Note:
    note = _own_note(db, note_id, user)
    note.title, note.text = body.title, body.text
    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)) -> None:
    note = _own_note(db, note_id, user)
    db.delete(note)
    db.commit()
