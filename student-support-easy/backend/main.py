"""Start the API and its background Gmail watcher."""
import asyncio
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from backend import database, background
from backend.routes import router


@asynccontextmanager
async def lifespan(app):
    database.setup()
    watcher = asyncio.create_task(background.watch_gmail())
    yield
    watcher.cancel()
    with suppress(asyncio.CancelledError):
        await watcher


app = FastAPI(title="Student Support Easy: BIA email to meeting", lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])
app.include_router(router)

# After a Vite build, this one server can also serve the React page.
frontend = Path(__file__).resolve().parents[1] / "frontend/dist"
if frontend.exists():
    app.mount("/", StaticFiles(directory=frontend, html=True), name="react")
