# The five database actions every table needs: list, get one, create, update, delete.
# Writing them once here keeps the rest of the app very short.

from fastapi import HTTPException
from sqlmodel import Session, select


def list_all(session: Session, model):
    """Return every row of a table."""
    return session.exec(select(model)).all()


def get_one(session: Session, model, item_id: int):
    """Return one row by id, or show a clean 404 error."""
    item = session.get(model, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} {item_id} not found")
    return item


def save(session: Session, item):
    """Write a row to the database and return the fresh version of it."""
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def create(session: Session, model, data: dict):
    """Make a new row from a plain dictionary of values."""
    return save(session, model(**data))


def update(session: Session, model, item_id: int, data: dict):
    """Change only the fields that were sent, leave the rest as they are."""
    item = get_one(session, model, item_id)
    for field, value in data.items():
        setattr(item, field, value)
    return save(session, item)


def delete(session: Session, model, item_id: int):
    """Remove one row."""
    session.delete(get_one(session, model, item_id))
    session.commit()
    return {"deleted": item_id}
