"""Find a free 30 minutes, then create a meeting for the sender."""
import hashlib
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from googleapiclient.errors import HttpError
from backend.settings import CALENDAR, TIMEZONE

ZONE = ZoneInfo(TIMEZONE)


def next_free_time(calendar, current=None):
    current = current or datetime.now(ZONE)
    result = calendar.freebusy().query(body={"timeMin": current.isoformat(),
        "timeMax": (current + timedelta(days=30)).isoformat(), "items": [{"id": CALENDAR}]}).execute()
    information = result.get("calendars", {}).get(CALENDAR)
    if information is None or information.get("errors"):
        raise ValueError("Calendar availability could not be checked.")
    busy = [(datetime.fromisoformat(b["start"].replace("Z", "+00:00")),
             datetime.fromisoformat(b["end"].replace("Z", "+00:00"))) for b in information.get("busy", [])]
    current = current.replace(second=0, microsecond=0) + timedelta(minutes=1)
    for day in range(30):
        opening = (current + timedelta(days=day)).replace(hour=9, minute=0)
        closing = opening.replace(hour=17)
        start = max(current, opening)
        for busy_start, busy_end in sorted(busy):
            if busy_end <= start or busy_start >= closing:
                continue
            if start + timedelta(minutes=30) <= busy_start:
                break
            start = busy_end.astimezone(ZONE)
            if start.second or start.microsecond:
                start += timedelta(minutes=1)
            start = start.replace(second=0, microsecond=0)
        if start + timedelta(minutes=30) <= closing:
            return start, start + timedelta(minutes=30)
    raise ValueError("No free session was found in the next 30 days.")


def find_or_create(calendar, email):
    # The same email always gets the same event ID, even after a restart.
    event_id = hashlib.sha256(("easy:" + email["id"]).encode()).hexdigest()
    try:
        event = calendar.events().get(calendarId=CALENDAR, eventId=event_id).execute()
        if event.get("status") == "cancelled":
            raise ValueError("The meeting was cancelled; inspect it before retrying.")
        return event
    except HttpError as error:
        if error.resp.status != 404:
            raise
    start, end = next_free_time(calendar)
    event = {"id": event_id, "summary": "BIA support: " + email["subject"][:150],
             "start": {"dateTime": start.isoformat(), "timeZone": TIMEZONE},
             "end": {"dateTime": end.isoformat(), "timeZone": TIMEZONE},
             "attendees": [{"email": email["sender"]}]}
    return calendar.events().insert(calendarId=CALENDAR, body=event, sendUpdates="all").execute()


def display_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(ZONE).strftime("%d %b, %I:%M %p IST")
