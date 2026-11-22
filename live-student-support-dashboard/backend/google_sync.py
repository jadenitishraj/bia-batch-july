"""Read-only Google polling. No connector tokens or browser cookies are used."""
import os
import re
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/calendar.events.readonly']
REFERENCE = re.compile(r'\[(SUP-[A-Z0-9-]{3,48})\]')


def reference(text):
    matches = set(REFERENCE.findall(text or ''))
    return next(iter(matches)) if len(matches) == 1 else None


def token_path():
    return Path(os.getenv('GOOGLE_TOKEN_FILE', '.local/google-token.json'))


def save_token(credentials, path=None):
    path = Path(path) if path else token_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic replacement and owner-only permissions, including the temporary file.
    temp = path.with_suffix('.tmp')
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(credentials.to_json())
    temp.chmod(0o600)
    temp.replace(path)


def poll(store):
    credentials = Credentials.from_authorized_user_file(str(token_path()), SCOPES)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        save_token(credentials)
    gmail = build('gmail', 'v1', credentials=credentials, cache_discovery=False)
    calendar = build('calendar', 'v3', credentials=credentials, cache_discovery=False)
    events = []
    page = None
    query = os.getenv('GMAIL_QUERY', 'label:BIA-Support')
    if not query.strip().startswith('label:'):
        raise ValueError('GMAIL_QUERY must start with a dedicated classroom label.')
    while True:
        result = gmail.users().messages().list(userId='me', q=query, maxResults=100, pageToken=page).execute()
        for message in result.get('messages', []):
            # Headers only: no bodies, attachments, snippets, or sender addresses retained.
            item = gmail.users().messages().get(userId='me', id=message['id'], format='metadata', metadataHeaders=['Subject']).execute()
            subject = next((h['value'] for h in item.get('payload', {}).get('headers', []) if h['name'].lower() == 'subject'), '')
            ref = reference(subject)
            if ref:
                from datetime import datetime, timezone
                received = datetime.fromtimestamp(int(item['internalDate']) / 1000, timezone.utc).isoformat() if item.get('internalDate') else None
                events.append(dict(source='gmail', event_id=message['id'], ref=ref, title=subject[:200],
                                   received_at=received, trusted_google=True))
        page = result.get('nextPageToken')
        if not page:
            break
    calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
    checkpoint_key = 'calendar_sync:' + calendar_id
    sync = store.checkpoint(checkpoint_key)
    page = None
    while True:
        args = dict(calendarId=calendar_id, showDeleted=True, maxResults=250, pageToken=page)
        if sync:
            args['syncToken'] = sync
        try:
            result = calendar.events().list(**args).execute()
        except HttpError as error:
            if error.resp.status == 410 and sync:
                # Expired token: restart a full scan; receipt keys make replay safe.
                sync, page = None, None
                continue
            raise
        for item in result.get('items', []):
            calendar_key = calendar_id + ':' + item['id']
            cancelled = item.get('status') == 'cancelled'
            ref = reference(item.get('summary', '')) or (store.calendar_ref(calendar_key) if cancelled else None)
            # Recurring series are intentionally excluded for this introductory lesson.
            if not ref or item.get('recurrence') or item.get('recurringEventId'):
                continue
            start = item.get('start', {}).get('dateTime') or item.get('start', {}).get('date')
            if not cancelled and not start:
                continue
            from backend.store import now
            version = item.get('updated') or now()
            from datetime import datetime, timedelta, timezone
            version = datetime.fromisoformat(version.replace('Z', '+00:00')).astimezone(timezone.utc)
            if cancelled and not item.get('updated'):
                previous = store.calendar_version(calendar_key)
                if previous:
                    version = max(version, datetime.fromisoformat(previous) + timedelta(microseconds=1))
            version = version.isoformat()
            events.append(dict(source='calendar', event_id=calendar_key + ':' + item.get('etag', 'cancelled' if cancelled else version),
                               ref=ref, calendar_id=calendar_key, version=version,
                               cancelled=cancelled, start=start))
        page = result.get('nextPageToken')
        if not page:
            # The caller saves this checkpoint ONLY after all returned changes commit.
            return events, checkpoint_key, result['nextSyncToken']
