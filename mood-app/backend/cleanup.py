# Keeps notes tidy when something they point at gets deleted.
# Example: if you delete the "Work" category, notes in it simply become uncategorised.

from sqlmodel import Session, select

from models import Category, Mood, Note, NoteTagLink, Tag

# Which column on Note belongs to which table
NOTE_FIELDS = {Category: "category_id", Mood: "mood_id"}


def detach_from_notes(session: Session, model, item_id: int):
    """Remove a category / mood / tag from every note that is still using it."""
    if model is Tag:
        links = session.exec(select(NoteTagLink).where(NoteTagLink.tag_id == item_id)).all()
        for link in links:
            session.delete(link)
        return

    field = NOTE_FIELDS.get(model)
    if field is None:
        return

    notes = session.exec(select(Note).where(getattr(Note, field) == item_id)).all()
    for note in notes:
        setattr(note, field, None)
        session.add(note)
