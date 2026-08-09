# The starting point of the backend.
# It creates the database, allows the browser to call us, and plugs in all the routes.

from dotenv import load_dotenv

load_dotenv()  # reads OPENAI_API_KEY from the .env file

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import create_tables
from models import Category, Mood, Tag
from routers import chat, notes
from routers.simple_crud import make_crud_router
from schemas import CategoryIn, MoodIn, TagIn
from seed import add_starter_data

create_tables()
add_starter_data()

app = FastAPI(title="Notes App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notes.router)
app.include_router(make_crud_router(Category, CategoryIn, "categories"))
app.include_router(make_crud_router(Tag, TagIn, "tags"))
app.include_router(make_crud_router(Mood, MoodIn, "moods"))
app.include_router(chat.router)


@app.get("/")
def home():
    return {"message": "Notes API is running. Open /docs to try it out."}
