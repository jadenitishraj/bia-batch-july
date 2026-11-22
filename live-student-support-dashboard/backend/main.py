import asyncio
import contextlib
import os
import re
import subprocess
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, model_validator

from backend.store import Store, now
from backend import google_sync, chat, automation, reporting

load_dotenv()
store = Store(os.getenv('DATABASE_PATH', '.local/support.sqlite3'))
clients = set()
authorization_process = None
automation_authorization_process = None
reply_tasks = {}
reply_subscribers = {}
lock = asyncio.Lock()
google_state = {'state': 'not_connected', 'last_poll': None, 'message': 'Authorize Google to enable read-only polling.'}
ALLOWED_ORIGINS = {'http://127.0.0.1:5173', 'http://localhost:5173', 'http://127.0.0.1:8000', 'http://localhost:8000'}


class SourceEvent(BaseModel):
    source: Literal['gmail', 'calendar']
    event_id: str = Field(min_length=1, max_length=300)
    ref: str = Field(pattern=r'^SUP-[A-Z0-9-]{3,48}$')
    title: str = Field(default='Student support request', min_length=1, max_length=200)
    calendar_id: str | None = Field(default=None, max_length=300)
    version: datetime | None = None
    cancelled: bool = False
    start: str | None = Field(default=None, max_length=80)

    @model_validator(mode='after')
    def validate_calendar(self):
        if self.source == 'calendar':
            if not self.calendar_id or not self.version or not self.version.tzinfo:
                raise ValueError('Calendar events need calendar_id and a timezone-aware version.')
            if not self.cancelled:
                if not self.start:
                    raise ValueError('An active tutoring event needs start.')
                datetime.fromisoformat(self.start.replace('Z', '+00:00'))
        return self

    def event(self):
        data = self.model_dump()
        if self.version:
            data['version'] = self.version.astimezone(timezone.utc).isoformat()
        return data


class StatusChange(BaseModel):
    status: Literal['new', 'in_progress', 'scheduled', 'needs_follow_up', 'resolved']


def snapshot():
    key, model = chat.configuration()
    return {**store.snapshot(), 'google': {**google_state, 'client_configured': Path(os.getenv('GOOGLE_CLIENT_FILE', '.local/google-client.json')).is_file()}, 'gemini': {'configured': bool(key), 'model': model}, 'automation': {**automation.public_state(store), 'authorizing': automation_authorization_process is not None and automation_authorization_process.poll() is None}, 'jobs': store.public_jobs()}


async def send(ws, data):
    try:
        await asyncio.wait_for(ws.send_json(data), timeout=2)
    except Exception:
        clients.discard(ws)
        with contextlib.suppress(Exception):
            await ws.close()


async def broadcast():
    # Called while holding lock, so updates and initial snapshots have one order.
    data = snapshot()
    await asyncio.gather(*(send(ws, data) for ws in list(clients)))


async def ingest(event):
    async with lock:
        changed = store.apply(event)  # SQLite commits here, before any network send.
        if changed:
            await broadcast()
        return changed


def prepare_demo():
    ref = 'SUP-' + uuid.uuid4().hex[:8].upper()
    current = datetime.now(timezone.utc)
    mail = dict(source='gmail', event_id='demo-mail:' + ref, ref=ref,
                title='[' + ref + '] Help understanding FastAPI background tasks')
    calendar = dict(source='calendar', event_id='demo-book:' + ref, ref=ref,
                    calendar_id='demo-calendar:' + ref, version=current.isoformat(),
                    cancelled=False, start=(current + timedelta(days=1)).isoformat())
    moved = {**calendar, 'event_id': 'demo-move:' + ref,
             'version': (current + timedelta(seconds=1)).isoformat(),
             'start': (current + timedelta(days=1, hours=1)).isoformat()}
    # Persist the whole classroom sequence before acknowledging the button click.
    import json
    with store.connect() as db:
        for index, event in enumerate([mail, calendar, moved]):
            db.execute('INSERT INTO pending_demo(payload,due) VALUES (?,?)',
                       (json.dumps(event), (current + timedelta(seconds=index * 2)).isoformat()))
    return ref


async def demo_worker():
    import json
    while True:
        with store.connect() as db:
            row = db.execute('SELECT * FROM pending_demo WHERE due<=? ORDER BY id LIMIT 1', (now(),)).fetchone()
        if row:
            await ingest(json.loads(row['payload']))
            # A crash between apply and delete safely replays through receipt deduplication.
            with store.connect() as db:
                db.execute('DELETE FROM pending_demo WHERE id=?', (row['id'],))
        await asyncio.sleep(0.25)


async def google_worker():
    while True:
        if authorization_process is not None and authorization_process.poll() is None:
            google_state.update(state='authorizing', message='Approve read-only access in the Google browser window.')
        elif google_sync.token_path().is_file():
            try:
                events, key, checkpoint = await asyncio.to_thread(google_sync.poll, store)
                for event in events:
                    await ingest(event)
                store.checkpoint(key, checkpoint)
                google_state.update(state='connected', last_poll=now(), message='Read-only polling is active.')
            except Exception:
                # Never echo Google response bodies, authorization URLs, or tokens to the UI/log.
                google_state.update(state='error', message='Google poll failed. Check API access, classroom label/calendar and OAuth consent; reauthorize if needed.')
        else:
            google_state.update(state='not_connected', message='Run the Google authorization step in the README.')
        async with lock:
            await broadcast()
        await asyncio.sleep(max(10, int(os.getenv('GOOGLE_POLL_SECONDS', '30'))))


async def automation_worker():
    while True:
        step = None
        try:
            step = asyncio.create_task(asyncio.to_thread(automation.run_one, store))
            changed = await asyncio.shield(step)
            if changed:
                async with lock:
                    await broadcast()
        except asyncio.CancelledError:
            if step:
                await step  # Do not abandon an in-flight external write during clean shutdown.
            raise
        except Exception:
            job = store.next_job()
            if job:
                store.job_update(job['ref'], job['stage'], 'Scheduling is paused because Google access is unavailable. Reconnect to continue safely.',
                                 error='Google access unavailable.', retry_at=(datetime.now(timezone.utc)+timedelta(minutes=5)).isoformat())
                async with lock:
                    await broadcast()
        await asyncio.sleep(1)


async def workflow_broadcast_worker(event):
    while True:
        await event.wait()
        event.clear()
        async with lock:
            await broadcast()


@asynccontextmanager
async def lifespan(app):
    with store.connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS pending_demo(id INTEGER PRIMARY KEY AUTOINCREMENT,payload TEXT NOT NULL,due TEXT NOT NULL)')
    store.interrupt_replies()
    workflow_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    store.workflow_notifier = lambda: loop.call_soon_threadsafe(workflow_event.set)
    workers = [asyncio.create_task(demo_worker()), asyncio.create_task(google_worker()), asyncio.create_task(automation_worker()), asyncio.create_task(workflow_broadcast_worker(workflow_event))]
    yield
    for process in [authorization_process, automation_authorization_process]:
        if process is not None and process.poll() is None:
            process.terminate()
    for worker in [*workers, *reply_tasks.values()]:
        worker.cancel()
    await asyncio.gather(*workers, *list(reply_tasks.values()), return_exceptions=True)
    store.interrupt_replies()
    store.workflow_notifier = None


app = FastAPI(title='Live Student Support Dashboard', lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1', 'localhost', 'testserver'])


@app.middleware('http')
async def local_origin(request: Request, call_next):
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        origin = request.headers.get('origin')
        if origin and origin not in ALLOWED_ORIGINS:
            return JSONResponse({'detail': 'Local classroom origins only.'}, status_code=403)
    return await call_next(request)


@app.get('/api/snapshot')
async def get_snapshot():
    return snapshot()


@app.get('/api/health')
async def health():
    return {'status': 'ok', 'cursor': store.snapshot()['cursor']}


@app.post('/api/google/connect', status_code=202)
async def connect_google():
    global authorization_process
    client = Path(os.getenv('GOOGLE_CLIENT_FILE', '.local/google-client.json'))
    if not client.is_file():
        raise HTTPException(503, 'Desktop OAuth client JSON is not configured yet. Complete Cloud Console setup first.')
    if authorization_process is None or authorization_process.poll() is not None:
        authorization_process = subprocess.Popen(
            [sys.executable, '-m', 'backend.authorize_google'],
            cwd=Path(__file__).resolve().parents[1], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    google_state.update(state='authorizing', message='Approve read-only access in the Google browser window.')
    async with lock:
        await broadcast()
    return {'message': 'Google consent opened in your default browser. Approve access there.'}


class AutomationActivation(BaseModel):
    enabled: bool


class ProposalApproval(BaseModel):
    revision: int = Field(ge=1)


@app.post('/api/automation/authorize', status_code=202)
async def authorize_automation():
    global automation_authorization_process
    if not Path(os.getenv('GOOGLE_CLIENT_FILE', '.local/google-client.json')).is_file():
        raise HTTPException(503, 'Desktop OAuth client is not configured.')
    if automation_authorization_process is None or automation_authorization_process.poll() is not None:
        automation_authorization_process = subprocess.Popen([sys.executable, '-m', 'backend.authorize_google', '--automation'],
            cwd=Path(__file__).resolve().parents[1], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {'message': 'Google consent opened. Monitoring stays off; every proposal still needs your approval before any invitation or email.'}


@app.post('/api/automation/demo', status_code=202)
async def proposal_simulation():
    ref = automation.prepare_simulation(store)
    async with lock:
        await broadcast()
    return {'ref':ref,'message':'Safe proposal simulation ready. Its approval creates only local fake outcomes; no Google invitation or email.'}


@app.post('/api/automation/activation')
async def activate_automation(body: AutomationActivation):
    try:
        await asyncio.to_thread(automation.activate, store, body.enabled)
    except ValueError as error:
        raise HTTPException(409, str(error))
    except Exception:
        raise HTTPException(503, 'Google automation access or availability preflight failed. Existing read-only operation is unchanged.')
    async with lock:
        await broadcast()
    return {'message': 'New-request proposal monitoring enabled. No existing requests will be backfilled; every meeting requires your approval.' if body.enabled else 'Proposal monitoring paused. Pending work is preserved.'}


@app.post('/api/proposals/{ref}/approve')
async def approve_proposal(ref: str, body: ProposalApproval):
    selected_job = store.job(ref)
    if not selected_job:
        raise HTTPException(404, 'Proposal not found.')
    if not selected_job['simulation'] and (not automation.public_state(store)['enabled'] or not automation.capable()):
        raise HTTPException(409, 'Enable proposal monitoring and complete additional Google consent first.')
    try:
        store.approve_job(ref, body.revision)
    except ValueError as error:
        raise HTTPException(409, str(error))
    async with lock:
        await broadcast()
    return {'message': 'Simulation approval saved. No real invitation or email will be sent.' if selected_job['simulation'] else 'Approval saved. The worker will recheck this exact time before creating the meeting, inviting the sender and sending the confirmation.'}


@app.get('/api/reports/{report_id}')
async def report_page(report_id: str, offset: int = 0):
    if offset < 0:
        raise HTTPException(422, 'Offset must be nonnegative.')
    try:
        return reporting.page(store, report_id, offset)
    except KeyError:
        raise HTTPException(404, 'Saved report not found.')


@app.get('/api/requests/{ref}/guests')
async def event_guests(ref: str):
    def fetch():
        with store.connect() as db:
            if not db.execute('SELECT 1 FROM requests WHERE ref=?', (ref,)).fetchone():
                raise KeyError(ref)
            job = db.execute('SELECT calendar_id,event_id,stage,simulation FROM support_jobs WHERE ref=?', (ref,)).fetchone()
            event = db.execute('SELECT id,cancelled FROM calendar_events WHERE ref=? ORDER BY version DESC,id DESC LIMIT 1', (ref,)).fetchone()
        if job and job['simulation']:
            return {'guests': [], 'message': 'Simulation only: no real meeting guests were invited.'}
        if job and job['stage'] in ['booked','acknowledging','acknowledged','send_uncertain']:
            calendar_id, event_id = job['calendar_id'], job['event_id']
        elif event:
            calendar_id, event_id = event['id'].rsplit(':', 1)
        else:
            return {'guests': [], 'message': 'No created or matched meeting is saved for this request.'}
        if calendar_id.startswith(('demo-', 'sample-')):
            return {'guests': [], 'message': 'Synthetic meeting: no real guests were invited.'}
        calendar = google_sync.build('calendar','v3',credentials=automation.load_credentials(google_sync.token_path()),cache_discovery=False)
        item = calendar.events().get(calendarId=calendar_id,eventId=event_id,maxAttendees=100,
                     fields='status,attendees(email,displayName,responseStatus),attendeesOmitted').execute()
        return {'guests': item.get('attendees', []), 'partial': item.get('attendeesOmitted', False), 'event_status': item.get('status')}
    try:
        return await asyncio.to_thread(fetch)
    except KeyError:
        raise HTTPException(404, 'Tracked request not found.')
    except Exception:
        raise HTTPException(503, 'Guest details could not be read from the tracked Calendar event. No unrelated event was queried.')


@app.post('/api/events')
async def source_event(event: SourceEvent):
    """Local simulator input, not a public Google webhook receiver."""
    try:
        return {'applied': await ingest(event.event())}
    except ValueError as error:
        raise HTTPException(409, str(error)) from error


@app.patch('/api/requests/{ref}')
async def change_status(ref: str, change: StatusChange):
    try:
        await ingest(dict(source='teacher', event_id=str(uuid.uuid4()), ref=ref, status=change.status))
    except KeyError:
        raise HTTPException(404, 'Request not found')
    return {'status': change.status}


@app.post('/api/demo', status_code=202)
async def demo():
    return {'ref': prepare_demo(), 'message': 'Saved demo: email, tutoring booking, then reschedule.'}



class ChatQuestion(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    request_id: uuid.UUID
    context_message_ids: list[str] | None = Field(default=None, max_length=10)


async def publish_reply(message_id, delta='', state=None, error=None):
    async with lock:
        message = store.update_reply(message_id, delta, state, error)
        # A complete replacement at a monotonic revision avoids duplicate token appends
        # when the initiating HTTP stream and WebSocket snapshot race each other.
        update = {'type': 'delta' if delta else 'done', 'message': message}
        for queue in reply_subscribers.get(message_id, set()):
            queue.put_nowait(update)
        await broadcast()
        return message


async def generate_reply(message_id, question, history, context):
    chunks = 0
    try:
        async with asyncio.timeout(90):
            async for text in chat.stream_reply(question, history, context):
                chunks += 1
                await publish_reply(message_id, delta=text)
        if chunks:
            await publish_reply(message_id, state='complete')
        else:
            await publish_reply(message_id, state='error', error='Gemini returned no text. Try a different question.')
    except asyncio.CancelledError:
        await publish_reply(message_id, state='interrupted', error='Reply interrupted by server shutdown. Send the question again.')
        raise
    except Exception as error:
        await publish_reply(message_id, state='error', error=chat.public_error(error))
    finally:
        reply_tasks.pop(message_id, None)


async def generate_local_reply(message_id, text):
    await publish_reply(message_id, delta=text)
    await publish_reply(message_id, state='complete')
    reply_tasks.pop(message_id, None)


@app.post('/api/chat')
async def ask(question: ChatQuestion):
    import json
    text = question.message.strip()
    if not text:
        raise HTTPException(422, 'Enter a question.')
    message_id = 'assistant:' + str(question.request_id)
    queue = asyncio.Queue()
    async with lock:
        existing = next((m for m in store.messages() if m['id'] == message_id), None)
        if len(reply_tasks) >= 2 and not existing:
            raise HTTPException(429, 'Two replies are already running. Wait for one to finish.')
        conversation = store.messages()
        history = [m for m in conversation if m['role'] in ('user', 'assistant')]
        previous = next((m['content'] for m in reversed(history) if m['role'] == 'user'), '')
        grounding_text = text + ' to this request' if re.search(r'\b(invited|invitees|guests|attendees)\b', text.lower()) and not chat.REFERENCE.search(text.upper()) else text
        context = chat.grounding(store, grounding_text, google_state.copy(), previous,
                                 conversation=conversation, visible_ids=question.context_message_ids)
        local_report = None
        action_reply = None
        approval_text = text.lower().replace('’', "'")
        simple_action = len(text) < 200 and '\n' not in text and not text.startswith(('"', "'", '`')) and not re.search(r"don't|do not|not yet|never", approval_text)
        approve = simple_action and bool(re.match(r'^(?:(?:ok(?:ay)?|yes)[,! ]+.*(?:go ahead|schedule|book|set up)|go ahead|approve\b|schedule (?:it|this|that)\b|book (?:it|this|that)\b)', approval_text)) and '?' not in text
        alternate = bool(re.search(r'\b(instead|check|available|free)\b', approval_text) and re.search(r'\d|\btomorrow\b|\btoday\b|\bafternoon\b|\bmorning\b|\bevening\b', approval_text)) and not chat.count_query(text)
        # Selecting a newly mentioned time is never approval of the old proposal.
        without_refs = chat.REFERENCE.sub('', text.upper()).lower()
        if approve and re.search(r'\d|\btomorrow\b|\btoday\b', without_refs):
            alternate, approve = True, False
        if approve or alternate:
            proposal = automation.pending_reference(store, text, question.context_message_ids)
            if not proposal:
                action_reply = 'Please identify the pending support reference or use its Approve button. I cannot choose between multiple proposals or approve a request without a saved proposal.'
            elif not proposal['simulation'] and (not automation.configuration(store).get('enabled') or not automation.capable()):
                action_reply = 'Additional Google consent and proposal monitoring are required first. No meeting or email was created.'
            elif alternate:
                try:
                    action_reply = await asyncio.to_thread(automation.propose_alternative, store, proposal['ref'], proposal['revision'], text)
                except ValueError as error:
                    action_reply = str(error)
                except Exception:
                    action_reply = 'Availability could not be verified. The pending proposal is unchanged; nothing was booked or sent.'
            else:
                visible = [m for m in conversation if question.context_message_ids is None or m['id'] in question.context_message_ids]
                seen = any(m.get('metadata', {}).get('ref') == proposal['ref'] and m.get('metadata', {}).get('proposal_revision') == proposal['revision'] for m in visible)
                if not seen:
                    action_reply = 'Please review the latest proposal time and use its targeted Approve button; an older proposal cannot be approved.'
                else:
                    try:
                        store.approve_job(proposal['ref'], proposal['revision'])
                        action_reply = ('Simulation approval saved for ' + proposal['ref'] + '. Only local fake outcomes will be recorded; no invitation or email will be sent.') if proposal['simulation'] else ('Approval saved for ' + proposal['ref'] + '. I will revalidate availability before creating that meeting, inviting the actual sender and sending the threaded confirmation.')
                    except ValueError as error:
                        action_reply = str(error)
            context = {'kind':'classroom','captured_at':now(),'source_cursor':store.snapshot()['cursor'],'google_state':google_state['state'],'last_successful_google_poll':google_state['last_poll'],'total_matching':1 if proposal else 0,'records':[]}
        elif reporting.requested(text) and not chat.count_query(text):
            context, local_report = reporting.make_report(store, text)
            context.update(source_cursor=store.snapshot()['cursor'],google_state=google_state['state'],last_successful_google_poll=google_state['last_poll'])
        elif re.search(r'\b(invited|invitees|guests|attendees)\b', approval_text) and context and len(context['records']) == 1:
            local_report = {'type':'guests', 'ref':context['records'][0]['ref']}
            context['intent'] = 'local_guests'
        if not chat.configuration()[0] and not action_reply:
            if local_report:
                action_reply = 'Here is the saved local report. Gemini is unavailable; the displayed records come directly from SQLite.'
            else:
                raise HTTPException(503, chat.public_error(RuntimeError('missing_key')))
        metadata = {'grounding_kind': 'classroom' if context else 'general', 'model': chat.configuration()[1]}
        if context:
            metadata.update(captured_at=context['captured_at'], source_cursor=context['source_cursor'],
                            google_state=context['google_state'], last_poll=context['last_successful_google_poll'],
                            matched=context['total_matching'], references=[r['ref'] for r in context['records']],
                            origins=sorted(origin for origin, count in context['aggregate']['by_origin'].items() if count) if context.get('aggregate') else sorted({r['origin'] for r in context['records']}),
                            resolved_references=(context.get('reference_resolution') or {}).get('references', []))
        if local_report:
            metadata['local_report'] = local_report
        if action_reply:
            metadata['local_action'] = True
        message, created = store.begin_reply(str(question.request_id), text, metadata)
        reply_subscribers.setdefault(message_id, set()).add(queue)
        if created:
            reply_tasks[message_id] = asyncio.create_task(generate_local_reply(message_id, action_reply) if action_reply else generate_reply(message_id, text, history, context))
            await broadcast()

    async def events():
        try:
            yield 'data: ' + json.dumps({'type': 'start', 'message': message}) + '\n\n'
            if message['state'] != 'streaming':
                yield 'data: ' + json.dumps({'type': 'done', 'message': message}) + '\n\n'
                return
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ': keepalive\n\n'
                    continue
                yield 'data: ' + json.dumps(item) + '\n\n'
                if item['message']['state'] != 'streaming':
                    break
        finally:
            reply_subscribers.get(message_id, set()).discard(queue)
            if not reply_subscribers.get(message_id):
                reply_subscribers.pop(message_id, None)

    return StreamingResponse(events(), media_type='text/event-stream',
                             headers={'Cache-Control': 'no-cache, no-transform', 'X-Accel-Buffering': 'no'})


@app.websocket('/ws')
async def updates(ws: WebSocket):
    if ws.headers.get('origin') and ws.headers['origin'] not in ALLOWED_ORIGINS:
        await ws.close(code=1008)
        return
    await ws.accept()
    async with lock:
        clients.add(ws)
        await send(ws, snapshot())
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        clients.discard(ws)


# After `npm run build`, one local FastAPI process can serve both UI and API.
from fastapi.staticfiles import StaticFiles
frontend_dist = Path(__file__).resolve().parents[1] / 'frontend' / 'dist'
if frontend_dist.exists():
    app.mount('/', StaticFiles(directory=frontend_dist, html=True), name='dashboard')
