# Fills the database with a few starter moods, categories, tags and notes.
# This only runs the very first time, when the database is still empty.

from sqlmodel import Session, select

from database import engine
from models import Category, Mood, Note, Tag

MOODS = [
    ("Happy", "😊", "#d97757"),
    ("Calm", "😌", "#7d9471"),
    ("Excited", "🤩", "#c15f3c"),
    ("Sad", "😔", "#8c8880"),
    ("Tired", "🥱", "#9b8aa6"),
]

CATEGORIES = [("Personal", "#cc785c"), ("Work", "#6e8b76"), ("Ideas", "#c99a5b")]

TAGS = [("family", "#b5785e"), ("goals", "#a38a5c"), ("learning", "#8a7ca8")]

# title, content, category, mood, tags
NOTES = [
    ("Morning walk", "Walked by the lake before work. The air was lovely.", "Personal", "Happy", ["family"]),
    ("Shipped the new feature", "The team released it today and everyone cheered.", "Work", "Happy", ["goals"]),
    ("App idea", "A notes app that understands how I feel.", "Ideas", "Excited", ["goals", "learning"]),
    ("Quiet evening", "Read a book with no phone nearby.", "Personal", "Calm", []),
    ("Long meeting day", "Too many calls, not enough deep work.", "Work", "Tired", []),
    ("Missing home", "Called my parents and felt a little homesick.", "Personal", "Sad", ["family"]),
]


def add_starter_data():
    """Create the starter rows, but only if there are no notes yet."""
    with Session(engine) as session:
        if session.exec(select(Note)).first():
            return

        for name, emoji, color in MOODS:
            session.add(Mood(name=name, emoji=emoji, color=color))
        for name, color in CATEGORIES:
            session.add(Category(name=name, color=color))
        for name, color in TAGS:
            session.add(Tag(name=name, color=color))
        session.commit()

        moods = {m.name: m for m in session.exec(select(Mood))}
        categories = {c.name: c for c in session.exec(select(Category))}
        tags = {t.name: t for t in session.exec(select(Tag))}

        for title, content, category, mood, tag_names in NOTES:
            note = Note(title=title, content=content)
            note.category = categories[category]
            note.mood = moods[mood]
            note.tags = [tags[name] for name in tag_names]
            session.add(note)
        session.commit()
