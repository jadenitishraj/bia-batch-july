# Chatbot tools for tags. Same four actions as categories: list, create, update, delete.

from agents import function_tool

import crud
from cleanup import detach_from_notes
from models import Tag
from tools.helpers import find_by_name, new_session


@function_tool
def list_tags() -> list[dict]:
    """List every tag the user has."""
    with new_session() as session:
        return [t.model_dump() for t in crud.list_all(session, Tag)]


@function_tool
def create_tag(name: str, color: str | None = None) -> dict:
    """Create a new tag. Color is a hex code like #a38a5c."""
    with new_session() as session:
        data = {"name": name, "color": color or "#a38a5c"}
        return crud.create(session, Tag, data).model_dump()


@function_tool
def update_tag(current_name: str, new_name: str | None = None, color: str | None = None) -> dict:
    """Rename a tag or change its color."""
    with new_session() as session:
        tag = find_by_name(session, Tag, current_name)
        if tag is None:
            return {"error": f"No tag called '{current_name}'"}
        changes = {"name": new_name or tag.name, "color": color or tag.color}
        return crud.update(session, Tag, tag.id, changes).model_dump()


@function_tool
def delete_tag(name: str) -> dict:
    """Delete a tag by name and take it off every note."""
    with new_session() as session:
        tag = find_by_name(session, Tag, name)
        if tag is None:
            return {"error": f"No tag called '{name}'"}
        detach_from_notes(session, Tag, tag.id)
        return crud.delete(session, Tag, tag.id)
