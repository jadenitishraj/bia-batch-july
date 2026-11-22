"""Use the consent already granted to this classroom application."""
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from backend.settings import GOOGLE_TOKEN


def clients():
    credentials = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN))
    required = ["gmail.readonly", "gmail.send", "calendar.events.owned", "calendar.events.freebusy"]
    scopes = ["https://www.googleapis.com/auth/" + name for name in required]
    if not credentials.has_scopes(scopes):
        raise ValueError("Complete the classroom Google consent first.")
    if credentials.expired:
        credentials.refresh(Request())
    gmail = build("gmail", "v1", credentials=credentials, cache_discovery=False)
    calendar = build("calendar", "v3", credentials=credentials, cache_discovery=False)
    return gmail, calendar
