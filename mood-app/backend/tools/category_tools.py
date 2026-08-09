# Chatbot tools for categories.
# Each function below becomes a button the chatbot can press, thanks to @function_tool.

from agents import function_tool

import crud
from cleanup import detach_from_notes
from models import Category
from tools.helpers import find_by_name, new_session


@function_tool
def list_categories() -> list[dict]:
    """List every category the user has."""
    with new_session() as session:
        return [c.model_dump() for c in crud.list_all(session, Category)]


@function_tool
def create_category(name: str, color: str | None = None) -> dict:
    """Create a new category. Color is a hex code like #cc785c."""
    with new_session() as session:
        data = {"name": name, "color": color or "#cc785c"}
        return crud.create(session, Category, data).model_dump()


@function_tool
def update_category(current_name: str, new_name: str | None = None, color: str | None = None) -> dict:
    """Rename a category or change its color."""
    with new_session() as session:
        category = find_by_name(session, Category, current_name)
        if category is None:
            return {"error": f"No category called '{current_name}'"}
        changes = {"name": new_name or category.name, "color": color or category.color}
        return crud.update(session, Category, category.id, changes).model_dump()


@function_tool
def delete_category(name: str) -> dict:
    """Delete a category by name. Notes inside it stay, they just lose the category."""
    with new_session() as session:
        category = find_by_name(session, Category, name)
        if category is None:
            return {"error": f"No category called '{name}'"}
        detach_from_notes(session, Category, category.id)
        return crud.delete(session, Category, category.id)
