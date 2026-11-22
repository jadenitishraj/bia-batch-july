"""Deterministic, approval-first Google booking. No model selects recipients or side effects."""
import base64
import hashlib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import getaddresses
from pathlib import Path
from zoneinfo import ZoneInfo
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_httplib2 import AuthorizedHttp
import httplib2
from backend.store import now
from backend import google_sync

EXTRA_SCOPES = ['https://www.googleapis.com/auth/gmail.send',
                'https://www.googleapis.com/auth/calendar.events.owned',
                'https://www.googleapis.com/auth/calendar.events.freebusy']
SCOPES = google_sync.SCOPES + EXTRA_SCOPES
ZONE = ZoneInfo('Asia/Kolkata')


def token_path():
    return Path(os.getenv('GOOGLE_AUTOMATION_TOKEN_FILE', '.local/google-automation-token.json'))


def capable():
    if not token_path().is_file():
        return False
    try:
        return Credentials.from_authorized_user_file(str(token_path())).has_scopes(SCOPES)
    except Exception:
        return False


def configuration(store):
    return json.loads(store.checkpoint('automation_config') or '{"enabled":false}')


def public_state(store):
    config = configuration(store)
    return dict(enabled=config.get('enabled', False), authorized=capable(),
                activated_at=config.get('activated_at'), calendar_id=os.getenv('GOOGLE_CALENDAR_ID', 'primary'))


def load_credentials(path):
    creds = Credentials.from_authorized_user_file(str(path))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        google_sync.save_token(creds, path)
    return creds


def services():
    creds = load_credentials(token_path())
    if not creds.has_scopes(SCOPES):
        raise ValueError('Additional automation consent is required.')
    return (build('gmail', 'v1', http=AuthorizedHttp(creds,http=httplib2.Http(timeout=20)), cache_discovery=False),
            build('calendar', 'v3', http=AuthorizedHttp(creds,http=httplib2.Http(timeout=20)), cache_discovery=False))


def activate(store, enabled):
    config = configuration(store)
    if not enabled:
        config['enabled'] = False
        store.checkpoint('automation_config', json.dumps(config))
        return
    gmail, calendar = services()
    reader = build('gmail', 'v1', credentials=load_credentials(google_sync.token_path()), cache_discovery=False)
    read_account = reader.users().getProfile(userId='me').execute()['emailAddress'].casefold()
    write_account = gmail.users().getProfile(userId='me').execute()['emailAddress'].casefold()
    if read_account != write_account:
        raise ValueError('Use the same Google account as the existing classroom connection.')
    # A read-only preflight: a failing busy calendar must never be treated as free.
    busy_intervals(calendar, datetime.now(timezone.utc), datetime.now(timezone.utc) + timedelta(hours=1))
    if not config.get('enabled'):
        config = dict(enabled=True, activated_at=now(), account_hash=hashlib.sha256(write_account.encode()).hexdigest())
    store.checkpoint('automation_config', json.dumps(config))


def busy_ids():
    return list(dict.fromkeys(['primary', os.getenv('GOOGLE_CALENDAR_ID', 'primary')] +
                              [v.strip() for v in os.getenv('GOOGLE_BUSY_CALENDAR_IDS', '').split(',') if v.strip()]))


def busy_intervals(calendar, start, end, calendar_id=None):
    ids = list(dict.fromkeys(busy_ids() + ([calendar_id] if calendar_id else [])))
    result = calendar.freebusy().query(body=dict(timeMin=start.isoformat(), timeMax=end.isoformat(),
                                      timeZone='Asia/Kolkata', items=[{'id': i} for i in ids])).execute()
    intervals = []
    for calendar_id in ids:
        entry = result.get('calendars', {}).get(calendar_id)
        if entry is None or entry.get('errors'):
            raise RuntimeError('Availability could not be verified for every configured calendar.')
        for interval in entry.get('busy', []):
            intervals.append((datetime.fromisoformat(interval['start'].replace('Z', '+00:00')),
                              datetime.fromisoformat(interval['end'].replace('Z', '+00:00'))))
    return intervals


def next_slot(current, busy, days=30):
    """Earliest minute-aligned free 30 minutes, 09:00–17:00 IST, every day."""
    current = current.astimezone(ZONE)
    current = current.replace(second=0, microsecond=0) + timedelta(minutes=1)
    for day in range(days):
        opening = (current + timedelta(days=day)).replace(hour=9, minute=0, second=0, microsecond=0)
        closing = opening.replace(hour=17)
        candidate = max(current, opening)
        for start, end in sorted(busy):
            if end <= candidate or start >= closing:
                continue
            if candidate + timedelta(minutes=30) <= start:
                break
            if candidate < end:
                candidate = end.astimezone(ZONE)
                candidate = candidate.replace(second=0, microsecond=0) + timedelta(minutes=bool(candidate.second or candidate.microsecond))
        if candidate + timedelta(minutes=30) <= closing:
            return candidate, candidate + timedelta(minutes=30)
    raise RuntimeError('No free 30-minute slot in the next 30 days; booking will retry later.')


def recover_event(calendar, calendar_id, event_id, ref):
    try:
        event = calendar.events().get(calendarId=calendar_id, eventId=event_id).execute()
    except HttpError as error:
        if error.resp.status == 404:
            return None
        raise
    if event.get('status') == 'cancelled':
        raise ValueError('The saved automatic meeting was cancelled; it will not be recreated.')
    if event.get('extendedProperties', {}).get('private', {}).get('biaJob') != event_id:
        raise ValueError('Calendar event identity conflict; manual review required.')
    return event


def original_message(gmail, message_id, ref):
    item = gmail.users().messages().get(userId='me', id=message_id, format='metadata',
            metadataHeaders=['Subject', 'From', 'Message-ID', 'References', 'Auto-Submitted', 'Precedence', 'List-Id']).execute()
    headers = {h['name'].lower(): h['value'] for h in item.get('payload', {}).get('headers', [])}
    if google_sync.reference(headers.get('subject', '')) != ref:
        raise ValueError('Source subject no longer has the expected unique support reference.')
    if headers.get('auto-submitted', 'no').lower() != 'no' or headers.get('list-id') or headers.get('precedence', '').lower() in ['bulk', 'list', 'junk']:
        raise ValueError('Automated/bulk email is not eligible for automatic replies.')
    addresses = getaddresses([headers.get('from', '')])
    if len(addresses) != 1 or not re.fullmatch(r'[^\s<>@,;\r\n]+@[^\s<>@,;\r\n]+\.[^\s<>@,;\r\n]+', addresses[0][1]):
        raise ValueError('A single valid actual sender address is required.')
    parent = headers.get('message-id', '')
    if not re.fullmatch(r'<[^<>\s\r\n]+@[^<>\s\r\n]+>', parent):
        raise ValueError('Original Message-ID is missing; threaded acknowledgment needs manual review.')
    subject = headers.get('subject', '')
    if '\r' in subject or '\n' in subject or len(subject) > 998:
        raise ValueError('Unsafe or oversized source subject; manual review required.')
    refs = re.findall(r'<[^<>\s\r\n]+@[^<>\s\r\n]+>', headers.get('references', ''))[-20:]
    return dict(recipient=addresses[0][1], thread_id=item['threadId'], parent_id=parent,
                reply_subject=subject if subject.lower().startswith('re:') else 'Re: ' + subject,
                references=' '.join(refs + [parent]))


def sent_match(gmail, rfc_id):
    result = gmail.users().messages().list(userId='me', q='in:sent rfc822msgid:' + rfc_id, maxResults=2).execute()
    return next(iter(result.get('messages', [])), {}).get('id')


def run_one(store, gmail=None, calendar=None, current=None):
    """One durable stage at a time. Ambiguous Gmail sends are reconciled, never resent."""
    config = configuration(store)
    with store.connect() as db:
        simulated = db.execute("SELECT * FROM support_jobs WHERE simulation=1 AND stage='approved' LIMIT 1").fetchone()
    if simulated:
        simulated = dict(simulated)
        store.job_update(simulated['ref'], 'booked', 'Simulation: meeting recorded locally. No real invitation was sent.')
        store.apply(dict(source='calendar',event_id='demo-approved:'+simulated['event_id'],ref=simulated['ref'],calendar_id='demo-calendar:'+simulated['event_id'],version=now(),cancelled=False,start=simulated['start']))
        store.job_update(simulated['ref'], 'acknowledged', 'Simulation: confirmation marked complete. No email was sent.', sent_id='simulation-only')
        return True
    if not config.get('enabled'):
        return False
    job = store.next_job()
    if not job:
        return False
    injected = gmail is not None
    gmail, calendar = (gmail, calendar) if injected else services()
    if not injected:
        account = gmail.users().getProfile(userId='me').execute()['emailAddress'].casefold()
        if hashlib.sha256(account.encode()).hexdigest() != config['account_hash']:
            store.job_update(job['ref'], 'failed', 'Google account changed. Reconnect the classroom account before retrying.', error='Google account mismatch.')
            return True
    calendar_id = job['calendar_id']
    try:
        if job['stage'] in ['send_uncertain', 'acknowledging']:
            found = sent_match(gmail, job['rfc_id'])
            if found:
                store.job_update(job['ref'], 'acknowledged', 'Booking confirmed; threaded acknowledgment verified in Sent.', sent_id=found, error=None)
            else:
                store.job_update(job['ref'], 'send_uncertain', 'Email delivery is uncertain. Checking Sent; no automatic resend.' if job['stage'] == 'acknowledging' else None, retry_at=(datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat())
            return True
        if job['stage'] in ['queued', 'preparing'] or (job['stage'] == 'retry_wait' and not job['start']):
            store.job_update(job['ref'], 'preparing', 'Checking availability for a proposal. No messages or invitations will be sent.')
            clock = current or datetime.now(timezone.utc)
            start, end = next_slot(clock, busy_intervals(calendar, clock, clock + timedelta(days=30), calendar_id))
            local = start.astimezone(ZONE).strftime('%d %b at %I:%M %p IST')
            store.job_update(job['ref'], 'awaiting_approval', 'I received this request. Shall I schedule a 30-minute session on ' + local + '?', start=start.isoformat(), end=end.isoformat(), error=None, retry_at=None)
            return True
        if job['stage'] == 'booking_uncertain':
            recovered = recover_event(calendar, calendar_id, job['event_id'], job['ref'])
            if not recovered:
                store.job_update(job['ref'], 'booking_uncertain', None, retry_at=(datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat())
                return True
        if not job['recipient']:
            store.job_update(job['ref'], 'approved', 'Preparing your approved booking and its threaded confirmation.')
            details = original_message(gmail, job['message_id'], job['ref'])
            store.job_update(job['ref'], 'approved', None, **details)
            job = store.job(job['ref'])
        event = recover_event(calendar, calendar_id, job['event_id'], job['ref'])
        if not event:
            if not job['booking_attempted']:
                start = datetime.fromisoformat(job['start'])
                end = datetime.fromisoformat(job['end'])
                clock = current or datetime.now(timezone.utc)
                occupied = start <= clock or any(a < end and b > start for a,b in busy_intervals(calendar, start, end, calendar_id))
                if occupied:
                    start, end = next_slot(clock, busy_intervals(calendar, clock, clock + timedelta(days=30), calendar_id))
                    local = start.astimezone(ZONE).strftime('%d %b at %I:%M %p IST')
                    store.job_update(job['ref'], 'awaiting_approval', 'The approved time is no longer free. Shall I schedule ' + local + ' instead? Fresh approval is required.', start=start.isoformat(), end=end.isoformat(), error=None, retry_at=None)
                    return True
                store.job_update(job['ref'], 'booking', 'Availability verified. Creating your approved tutoring meeting and sender invitation.', booking_attempted=1)
                job = store.job(job['ref'])
            if datetime.fromisoformat(job['start']) <= (current or datetime.now(timezone.utc)):
                store.job_update(job['ref'], 'failed', 'The approved time elapsed before booking could be confirmed. Review Calendar before requesting another proposal.', error='Approved time elapsed; manual review required.')
                return True
            body = dict(id=job['event_id'], summary='[' + job['ref'] + '] Support tutoring',
                        start={'dateTime': job['start'], 'timeZone': 'Asia/Kolkata'},
                        end={'dateTime': job['end'], 'timeZone': 'Asia/Kolkata'},
                        attendees=[{'email': job['recipient']}], transparency='opaque',
                        extendedProperties={'private': {'biaJob': job['event_id'], 'supportRef': job['ref']}})
            try:
                event = calendar.events().insert(calendarId=calendar_id, body=body, sendUpdates='all').execute()
            except Exception as error:
                status = getattr(getattr(error, 'resp', None), 'status', None)
                if status in [400,401,403,404]:
                    raise ValueError('Calendar rejected the approved booking; manual review required.') from error
                if status == 429:
                    store.job_update(job['ref'],'retry_wait','Calendar rate limit reached. The approved time will be rechecked before a safe retry.',booking_attempted=0,retry_at=(datetime.now(timezone.utc)+timedelta(minutes=5)).isoformat())
                    return True
                # A timeout or 409 can mean insert succeeded: reconcile the deterministic ID.
                event = recover_event(calendar, calendar_id, job['event_id'], job['ref'])
                if not event:
                    store.job_update(job['ref'], 'booking_uncertain', 'Calendar creation outcome is uncertain. Checking the saved event ID; no new booking or email will be attempted.', error='Calendar result needs reconciliation.', retry_at=(datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat())
                    return True
        start = event['start'].get('dateTime')
        end = event['end'].get('dateTime')
        if not start or not end:
            raise ValueError('Recovered meeting has no timed session; manual review required.')
        store.job_update(job['ref'], 'booked', 'Tutoring booked; Calendar invitation requested for the actual sender.',
                         start=start, end=end, error=None, retry_at=None)
        job = store.job(job['ref'])
        # Search before the first send as well as after any crash/ambiguous outcome.
        existing = sent_match(gmail, job['rfc_id'])
        if existing:
            store.job_update(job['ref'], 'acknowledged', 'Threaded acknowledgment verified in Sent.', sent_id=existing, error=None)
            return True
        email = EmailMessage()
        email['To'] = job['recipient']
        email['From'] = gmail.users().getProfile(userId='me').execute()['emailAddress']
        email['Subject'] = job['reply_subject']
        email['Message-ID'] = job['rfc_id']
        email['In-Reply-To'] = job['parent_id']
        email['References'] = job['references']
        local = datetime.fromisoformat(start.replace('Z', '+00:00')).astimezone(ZONE).strftime('%d %b %Y at %I:%M %p IST')
        email.set_content(f"We received your support request [{job['ref']}]. Your 30-minute tutoring session is scheduled for {local}. A Google Calendar invitation has been sent to this address. Please reply in this thread if you need help or a different time.\n\nBIA Classroom Support")
        store.job_update(job['ref'], 'acknowledging', 'Sending the threaded booking acknowledgment.')
        try:
            sent = gmail.users().messages().send(userId='me', body={'threadId': job['thread_id'], 'raw': base64.urlsafe_b64encode(email.as_bytes()).decode()}).execute()
        except Exception as error:
            status = getattr(getattr(error, 'resp', None), 'status', None)
            if status in [400, 401, 403, 404, 429]:
                store.job_update(job['ref'], 'retry_wait', 'Booking exists, but acknowledgment was rejected. It will retry safely.', error='Gmail rejected acknowledgment (' + str(status) + ').', retry_at=(datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat())
            else:
                store.job_update(job['ref'], 'send_uncertain', 'Email delivery is uncertain. Checking Sent; no automatic resend.', error='Uncertain Gmail send outcome.', retry_at=(datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat())
            return True
        store.job_update(job['ref'], 'acknowledged', 'Booking confirmed; threaded acknowledgment sent.', sent_id=sent['id'], error=None)
    except Exception as error:
        # No raw API response or recipient is copied into public activity/model context.
        attempts = job['attempts'] + 1
        permanent = isinstance(error, ValueError) or attempts >= 5
        stage = 'failed' if permanent else 'retry_wait'
        store.job_update(job['ref'], stage, 'Support scheduling needs attention.' if permanent else 'Automatic booking paused; a safe retry is scheduled.',
                         error=(str(error) if isinstance(error,ValueError) and str(error).startswith(('Source subject','Automated/bulk','A single valid','Original Message-ID','Unsafe or oversized','The saved automatic','Calendar event identity','Recovered meeting','Calendar rejected')) else 'Manual review required.') if permanent else 'Google operation did not complete; retry scheduled.',
                         attempts=attempts, retry_at=None if permanent else (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat())
    return True


def pending_reference(store, text, visible_ids=None):
    from backend.chat import resolve_followup, REFERENCE
    refs = list(dict.fromkeys(REFERENCE.findall(text.upper())))
    pending = [j for j in store.public_jobs() if j['stage'] == 'awaiting_approval']
    if len(refs) > 1:
        return None
    if len(refs) == 1:
        return next((j for j in pending if j['ref'] == refs[0]), None)
    if len(pending) > 1:
        return None  # A generic go-ahead or time change must not choose between pending proposals.
    resolution = resolve_followup('what is the status of this?', store.messages(), visible_ids)
    if resolution and resolution['status'] == 'resolved':
        matches = [j for j in pending if j['ref'] in resolution['references']]
        if len(matches) == 1:
            return matches[0]
    # Multiple pending proposals require a target even if the latest notification is offscreen.
    return pending[0] if len(pending) == 1 else None


def alternative_time(text, proposal, current=None):
    text = text.lower().replace('a.m.', 'am').replace('p.m.', 'pm').replace('a.m', 'am').replace('p.m', 'pm')
    if re.search(r'\b(utc|gmt|est|edt|pst|pdt|cet|pacific|eastern)\b', text):
        raise ValueError('Please give the alternate time in India time (IST); I will not assume a conversion from another timezone.')
    if len(re.findall(r'\b\d{1,2}(?::[0-5]\d)?\s*(?:am|pm)\b|\b(?:[01]?\d|2[0-3]):[0-5]\d\b',text)) > 1:
        raise ValueError('Please select one candidate time for this proposal.')
    match = re.search(r'\b(\d{1,2})(?::([0-5]\d))?\s*(am|pm)\b|\b([01]?\d|2[0-3]):([0-5]\d)\b', text)
    if not match:
        raise ValueError('Please give a time with am/pm, or a 24-hour time such as 16:00, in India time.')
    clock = (current or datetime.now(timezone.utc)).astimezone(ZONE)
    if 'tomorrow' in text:
        date = clock.date() + timedelta(days=1)
    elif 'today' in text:
        date = clock.date()
    elif re.search(r'\b\d{4}-\d{2}-\d{2}\b', text):
        date = datetime.fromisoformat(re.search(r'\b\d{4}-\d{2}-\d{2}\b', text)[0]).date()
    elif re.search(r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|next week|january|february|march|april|may|june|july|august|september|october|november|december)\b|\b\d{1,2}(?:st|nd|rd|th)\b', text):
        raise ValueError('Please give the exact date (YYYY-MM-DD) for that alternate time.')
    else:
        date = datetime.fromisoformat(proposal['start']).astimezone(ZONE).date()
    if match[1]:
        hour = int(match[1])
        if not 1 <= hour <= 12:
            raise ValueError('Please use 1–12 with am/pm.')
        hour = hour % 12 + (12 if match[3] == 'pm' else 0)
        minute = int(match[2] or 0)
    else:
        hour, minute = int(match[4]), int(match[5])
    start = datetime.combine(date, datetime.min.time(), ZONE).replace(hour=hour, minute=minute)
    end = start + timedelta(minutes=30)
    if start <= clock or start.hour < 9 or end > start.replace(hour=17, minute=0):
        raise ValueError('Choose a future 30-minute slot entirely between 9:00 am and 5:00 pm India time (latest start 4:30 pm).')
    return start, end


def propose_alternative(store, ref, revision, text, calendar=None, current=None):
    proposal = store.job(ref)
    if not proposal or proposal['stage'] != 'awaiting_approval' or proposal['revision'] != revision:
        raise ValueError('That pending proposal changed. Review the latest proposal first.')
    start, end = alternative_time(text, proposal, current)
    calendar = calendar or (None if proposal['simulation'] else services()[1])
    intervals = [] if proposal['simulation'] else busy_intervals(calendar, start, end, proposal['calendar_id'])
    if any(a < end and b > start for a,b in intervals):
        store.job_update(ref, 'awaiting_approval', 'That alternate time is occupied. The previous proposal is unchanged; no meeting or email was created.')
        return 'That time is occupied. The pending proposal was kept; you can check another time.'
    local = start.strftime('%d %b at %I:%M %p IST')
    store.job_update(ref, 'awaiting_approval', 'The alternate time is free: ' + local + '. Shall I schedule it? Fresh approval is required.', start=start.isoformat(), end=end.isoformat())
    return ('Simulation only: availability is assumed free, with no Google check. ' if proposal['simulation'] else '') + 'The alternate is available and is now the pending proposal. Approve it to create the meeting and send the invitation and confirmation.'


def prepare_simulation(store):
    import uuid
    ref = 'SUP-PROPOSAL-' + uuid.uuid4().hex[:6].upper()
    store.apply(dict(source='gmail',event_id='demo-proposal:'+ref,ref=ref,title='['+ref+'] Safe proposal exercise'))
    start=(datetime.now(ZONE)+timedelta(days=1)).replace(hour=16,minute=0,second=0,microsecond=0)
    end=start+timedelta(minutes=30)
    event_id=hashlib.sha256(('simulation:'+ref).encode()).hexdigest()
    with store.connect() as db:
        db.execute('INSERT INTO support_jobs(ref,message_id,calendar_id,event_id,rfc_id,stage,start,end,updated_at,simulation) VALUES (?,?,?,?,?,?,?,?,?,1)',
                   (ref,'demo:'+ref,'simulation-only',event_id,'<demo-'+event_id+'@classroom.local>','queued',start.isoformat(),end.isoformat(),now()))
    store.job_update(ref,'awaiting_approval','Simulation: shall I schedule tomorrow at 4:00 pm India time? Approving records a fake meeting and fake confirmation locally; nothing is sent.')
    return ref
