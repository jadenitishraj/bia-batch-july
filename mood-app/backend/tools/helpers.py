# Small helpers shared by all the chatbot tools.
# They open a database connection and turn rows into plain, readable dictionaries.

from sqlmodel import Session, col, select

from database import engine


def new_session() -> Session:
    """Open a fresh database session for one tool call."""
    return Session(engine)


def find_by_name(session: Session, model, name: str | None):
    """Find a category / tag / mood by name, ignoring capital letters."""
    if not name:
        return None
    return session.exec(select(model).where(col(model.name).ilike(name))).first()


def note_summary(note) -> dict:
    """Describe a note in words the chatbot can read easily."""
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "category": note.category.name if note.category else None,
        "mood": note.mood.name if note.mood else None,
        "tags": [tag.name for tag in note.tags],
        "created_at": note.created_at.strftime("%d %b %Y"),
    }
