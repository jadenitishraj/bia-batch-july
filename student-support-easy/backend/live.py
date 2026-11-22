"""A WebSocket pushes saved data to each open browser."""
import asyncio
from backend import database

browsers = set()
google_status = "Connecting"


def snapshot():
    return {**database.snapshot(), "google": google_status}


async def broadcast():
    for browser in list(browsers):
        try:
            await asyncio.wait_for(browser.send_json(snapshot()), timeout=2)
        except Exception:
            browsers.discard(browser)
