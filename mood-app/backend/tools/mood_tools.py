# Chatbot tools for moods, for example "Happy 😊" or "Calm 😌".

from agents import function_tool

import crud
from cleanup import detach_from_notes
from models import Mood
from tools.helpers import find_by_name, new_session


@function_tool
def list_moods() -> list[dict]:
    """List every mood the user can choose from."""
    with new_session() as session:
        return [m.model_dump() for m in crud.list_all(session, Mood)]


@function_tool
def create_mood(name: str, emoji: str | None = None, color: str | None = None) -> dict:
    """Create a new mood, for example name='Grateful' emoji='🙏'."""
    with new_session() as session:
        data = {"name": name, "emoji": emoji or "🙂", "color": color or "#d97757"}
        return crud.create(session, Mood, data).model_dump()


@function_tool
def update_mood(current_name: str, new_name: str | None = None, emoji: str | None = None, color: str | None = None) -> dict:
    """Rename a mood or change its emoji / color."""
    with new_session() as session:
        mood = find_by_name(session, Mood, current_name)
        if mood is None:
            return {"error": f"No mood called '{current_name}'"}
        changes = {
            "name": new_name or mood.name,
            "emoji": emoji or mood.emoji,
            "color": color or mood.color,
        }
        return crud.update(session, Mood, mood.id, changes).model_dump()


@function_tool
def delete_mood(name: str) -> dict:
    """Delete a mood by name. Notes keep existing, they just lose that mood."""
    with new_session() as session:
        mood = find_by_name(session, Mood, name)
        if mood is None:
            return {"error": f"No mood called '{name}'"}
        detach_from_notes(session, Mood, mood.id)
        return crud.delete(session, Mood, mood.id)
