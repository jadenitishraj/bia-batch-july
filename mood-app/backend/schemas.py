# The shape of the data going in and out of the API.
# Tables (models.py) are what we store; schemas are what the browser sends and receives.

from datetime import datetime
from sqlmodel import SQLModel

from models import Category, Mood, Tag


class CategoryIn(SQLModel):
    name: str
    color: str = "#cc785c"


class TagIn(SQLModel):
    name: str
    color: str = "#a38a5c"


class MoodIn(SQLModel):
    name: str
    emoji: str = "🙂"
    color: str = "#d97757"


class NoteIn(SQLModel):
    """What the browser sends when creating or editing a note."""

    title: str
    content: str = ""
    category_id: int | None = None
    mood_id: int | None = None
    tag_ids: list[int] = []


class NoteOut(SQLModel):
    """What we send back: a note with its category, mood and tags already filled in."""

    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    category: Category | None = None
    mood: Mood | None = None
    tags: list[Tag] = []


class ChatIn(SQLModel):
    """One message from the user, plus the conversation so far."""

    message: str
    history: list[dict] = []


class ExplainIn(SQLModel):
    """One recorded trace that we want explained in simple words."""

    trace: dict
