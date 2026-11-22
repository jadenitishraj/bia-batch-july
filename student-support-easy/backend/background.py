"""Check Gmail regularly while FastAPI serves the browser."""

import asyncio
from backend import database, gmail, google_login, workflow, live
from backend.settings import POLL_SECONDS


async def watch_gmail():
    while True:
        try:
            gmail_client, calendar_client = await asyncio.to_thread(
                google_login.clients
            )
            emails = await asyncio.to_thread(
                gmail.new_emails, gmail_client, database.first_start()
            )
            live.google_status = "Connected"
            for email in emails:
                await workflow.handle(email, gmail_client, calendar_client)
        except Exception:
            live.google_status = "Check Google consent or connection"
        await live.broadcast()
        await asyncio.sleep(POLL_SECONDS)
