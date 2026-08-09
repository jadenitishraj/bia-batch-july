# Chatbot tools for notes: search, write, edit, delete, and count notes per mood.
# The chatbot refers to categories, moods and tags by their name, not their id.

from collections import Counter
from datetime import datetime

from agents import function_tool
from sqlmodel import Session, col, select

import crud
from models import Category, Mood, Note, NoteTagLink, Tag
from tools.helpers import find_by_name, new_session, note_summary


def find_tags(session: Session, names: list[str] | None) -> list[Tag]:
    """Turn a list of tag names into real tag rows. Unknown names are skipped."""
    found = []
    for name in names or []:
        tag = find_by_name(session, Tag, name)
        if tag:
            found.append(tag)
    return found


@function_tool
def list_notes(
    search: str | None = None,
    category: str | None = None,
    mood: str | None = None,
    tag: str | None = None,
) -> list[dict]:
    """Find notes. Filter by a word in the text, a category name, a mood name or a tag name."""
    with new_session() as session:
        query = select(Note)
        if search:
            query = query.where(col(Note.title).contains(search) | col(Note.content).contains(search))

        category_row = find_by_name(session, Category, category)
        if category_row:
            query = query.where(Note.category_id == category_row.id)

        mood_row = find_by_name(session, Mood, mood)
        if mood_row:
            query = query.where(Note.mood_id == mood_row.id)

        tag_row = find_by_name(session, Tag, tag)
        if tag_row:
            query = query.join(NoteTagLink).where(NoteTagLink.tag_id == tag_row.id)

        return [note_summary(note) for note in session.exec(query).all()]


@function_tool
def count_notes_by_mood() -> dict:
    """Count how many notes were written in each mood, e.g. how many times the user was happy."""
    with new_session() as session:
        notes = crud.list_all(session, Note)
        return dict(Counter(note.mood.name if note.mood else "No mood" for note in notes))


@function_tool
def create_note(
    title: str,
    content: str | None = None,
    category: str | None = None,
    mood: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Write a new note. The category, mood and tags must already exist."""
    with new_session() as session:
        note = Note(title=title, content=content or "")
        note.category = find_by_name(session, Category, category)
        note.mood = find_by_name(session, Mood, mood)
        note.tags = find_tags(session, tags)
        return note_summary(crud.save(session, note))


@function_tool
def update_note(
    note_id: int,
    title: str | None = None,
    content: str | None = None,
    category: str | None = None,
    mood: str | None = None,
    tags: list[str] | None = None,
) -> dict:
    """Edit a note. Use list_notes first to find its id. Only the values you pass are changed."""
    with new_session() as session:
        note = session.get(Note, note_id)
        if note is None:
            return {"error": f"No note with id {note_id}"}
        if title:
            note.title = title
        if content:
            note.content = content
        if category:
            note.category = find_by_name(session, Category, category)
        if mood:
            note.mood = find_by_name(session, Mood, mood)
        if tags:
            note.tags = find_tags(session, tags)
        note.updated_at = datetime.now()
        return note_summary(crud.save(session, note))


@function_tool
def delete_note(note_id: int) -> dict:
    """Delete a note. Use list_notes first to find its id."""
    with new_session() as session:
        return crud.delete(session, Note, note_id)
