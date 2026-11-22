"""One email becomes one meeting. Read the steps from top to bottom."""

import asyncio
from backend import database, gmail, calendar, live


async def handle(email, gmail_client, calendar_client):
    # Gmail may return the same email again. Handle each email only once.
    if database.request(email["id"]):
        return
    database.remember(email)

    try:
        # 1. Show the new request in the chat and table.
        database.add_notice(
            email["id"] + ":received", "You received a BIA email: " + email["subject"]
        )
        await live.broadcast()

        # 2. Create the meeting and save its time.
        event = await asyncio.to_thread(calendar.find_or_create, calendar_client, email)
        meeting = calendar.display_time(event["start"]["dateTime"])
        database.save_status(email["id"], "scheduled", meeting)
        await live.broadcast()

        # 3. Email the sender, then mark the request as done.
        await asyncio.to_thread(gmail.send_confirmation, gmail_client, email, meeting)
        database.save_status(email["id"], "done")
        database.add_notice(
            email["id"] + ":done",
            "Meeting scheduled for " + meeting + ". Confirmation email sent.",
        )
    except Exception:
        # Stop here if Google fails. Recorded emails are never retried automatically.
        database.save_status(
            email["id"],
            "needs review",
            error="Check Calendar and Sent before trying again.",
        )
        database.add_notice(
            email["id"] + ":error",
            "This request needs review. Check Calendar and Sent.",
        )

    await live.broadcast()
