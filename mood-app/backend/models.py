# The shape of our data: Note, Category, Tag and Mood.
# SQLModel turns each class below into a real table in SQLite.

from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class NoteTagLink(SQLModel, table=True):
    """Join table: connects one note to many tags."""

    note_id: int | None = Field(default=None, foreign_key="note.id", primary_key=True)
    tag_id: int | None = Field(default=None, foreign_key="tag.id", primary_key=True)


class Category(SQLModel, table=True):
    """A folder-like label, for example "Work" or "Personal"."""

    id: int | None = Field(default=None, primary_key=True)
    name: str
    color: str = "#cc785c"


class Tag(SQLModel, table=True):
    """A small keyword you can stick on many notes."""

    id: int | None = Field(default=None, primary_key=True)
    name: str
    color: str = "#a38a5c"


class Mood(SQLModel, table=True):
    """How you felt while writing the note."""

    id: int | None = Field(default=None, primary_key=True)
    name: str
    emoji: str = "🙂"
    color: str = "#d97757"


class Note(SQLModel, table=True):
    """The note itself. It points to one category, one mood and many tags."""

    id: int | None = Field(default=None, primary_key=True)
    title: str
    content: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    category_id: int | None = Field(default=None, foreign_key="category.id")
    mood_id: int | None = Field(default=None, foreign_key="mood.id")

    category: Category | None = Relationship()
    mood: Mood | None = Relationship()
    tags: list[Tag] = Relationship(link_model=NoteTagLink)
