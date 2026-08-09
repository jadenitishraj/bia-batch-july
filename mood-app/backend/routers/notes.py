# The /notes routes. Notes need a little extra care because they carry a list of tags,
# and because you can filter them by category, mood, tag or a search word.

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlmodel import Session, col, select

import crud
from database import get_session
from models import Note, NoteTagLink, Tag
from schemas import NoteIn, NoteOut

router = APIRouter(prefix="/notes", tags=["notes"])


def pick_tags(session: Session, tag_ids: list[int]) -> list[Tag]:
    """Turn a list of tag ids into real Tag rows."""
    return list(session.exec(select(Tag).where(col(Tag.id).in_(tag_ids))).all())


@router.get("", response_model=list[NoteOut])
def list_notes(
    search: str | None = None,
    category_id: int | None = None,
    mood_id: int | None = None,
    tag_id: int | None = None,
    session: Session = Depends(get_session),
):
    """List notes, newest first, with optional filters."""
    query = select(Note)
    if search:
        query = query.where(col(Note.title).contains(search) | col(Note.content).contains(search))
    if category_id:
        query = query.where(Note.category_id == category_id)
    if mood_id:
        query = query.where(Note.mood_id == mood_id)
    if tag_id:
        query = query.join(NoteTagLink).where(NoteTagLink.tag_id == tag_id)
    return session.exec(query.order_by(col(Note.updated_at).desc())).all()


@router.get("/{note_id}", response_model=NoteOut)
def get_note(note_id: int, session: Session = Depends(get_session)):
    return crud.get_one(session, Note, note_id)


@router.post("", response_model=NoteOut)
def create_note(data: NoteIn, session: Session = Depends(get_session)):
    note = Note(**data.model_dump(exclude={"tag_ids"}))
    note.tags = pick_tags(session, data.tag_ids)
    return crud.save(session, note)


@router.put("/{note_id}", response_model=NoteOut)
def update_note(note_id: int, data: NoteIn, session: Session = Depends(get_session)):
    note = crud.get_one(session, Note, note_id)
    for field, value in data.model_dump(exclude={"tag_ids"}).items():
        setattr(note, field, value)
    note.tags = pick_tags(session, data.tag_ids)
    note.updated_at = datetime.now()
    return crud.save(session, note)


@router.delete("/{note_id}")
def delete_note(note_id: int, session: Session = Depends(get_session)):
    return crud.delete(session, Note, note_id)
