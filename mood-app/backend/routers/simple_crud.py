# Builds a ready-made set of CRUD routes for any simple table.
# Categories, tags and moods all work the same way, so we write the routes once here.

from fastapi import APIRouter, Depends
from sqlmodel import Session

import crud
from cleanup import detach_from_notes
from database import get_session


def make_crud_router(model, schema, name: str) -> APIRouter:
    """Give it a table + its input shape + a url name, get back 4 working routes."""
    router = APIRouter(prefix=f"/{name}", tags=[name])

    @router.get("")
    def list_items(session: Session = Depends(get_session)):
        return crud.list_all(session, model)

    @router.post("")
    def create_item(item: schema, session: Session = Depends(get_session)):
        return crud.create(session, model, item.model_dump())

    @router.put("/{item_id}")
    def update_item(item_id: int, item: schema, session: Session = Depends(get_session)):
        return crud.update(session, model, item_id, item.model_dump())

    @router.delete("/{item_id}")
    def delete_item(item_id: int, session: Session = Depends(get_session)):
        detach_from_notes(session, model, item_id)
        return crud.delete(session, model, item_id)

    return router
