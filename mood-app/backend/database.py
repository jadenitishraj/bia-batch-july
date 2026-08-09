# Sets up the SQLite database connection.
# Everything else in the app asks this file for a "session" to talk to the database.

from sqlmodel import SQLModel, Session, create_engine

# The whole database lives in one file next to this code: notes.db
engine = create_engine("sqlite:///notes.db", connect_args={"check_same_thread": False})


def create_tables():
    """Create the database tables (only creates what is missing)."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Give one database session to a request, then close it automatically."""
    with Session(engine) as session:
        yield session
