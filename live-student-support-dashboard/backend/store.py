"""One SQLite transaction = source receipt + projection + durable activity."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path):
        self.path = str(path)
        self.workflow_notifier = None
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS requests (
                    ref TEXT PRIMARY KEY, title TEXT NOT NULL, status TEXT NOT NULL,
                    session_at TEXT, updated_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS receipts (
                    source TEXT, event_id TEXT, PRIMARY KEY(source,event_id));
                CREATE TABLE IF NOT EXISTS activity (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT,
                    source TEXT NOT NULL, message TEXT NOT NULL, at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS calendar_events (
                    id TEXT PRIMARY KEY, ref TEXT NOT NULL, version TEXT NOT NULL,
                    cancelled INTEGER NOT NULL, start TEXT);
                CREATE TABLE IF NOT EXISTS request_details (
                    ref TEXT PRIMARY KEY, received_at TEXT NOT NULL, received_basis TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS support_jobs (
                    ref TEXT PRIMARY KEY, message_id TEXT NOT NULL, calendar_id TEXT NOT NULL,
                    event_id TEXT NOT NULL, rfc_id TEXT NOT NULL, stage TEXT NOT NULL,
                    start TEXT, end TEXT, recipient TEXT, thread_id TEXT, parent_id TEXT,
                    reply_subject TEXT, "references" TEXT, sent_id TEXT, error TEXT,
                    attempts INTEGER NOT NULL DEFAULT 0, retry_at TEXT,
                    revision INTEGER NOT NULL DEFAULT 1, updated_at TEXT NOT NULL,
                    booking_attempted INTEGER NOT NULL DEFAULT 0, simulation INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS report_snapshots(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS checkpoints (key TEXT PRIMARY KEY, value TEXT);
                CREATE TABLE IF NOT EXISTS chat_messages (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL, content TEXT NOT NULL, state TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}', at TEXT NOT NULL,
                    revision INTEGER NOT NULL DEFAULT 1);
            ''')
            if 'simulation' not in {row[1] for row in db.execute('PRAGMA table_info(support_jobs)')}:
                db.execute('ALTER TABLE support_jobs ADD COLUMN simulation INTEGER NOT NULL DEFAULT 0')
            columns = {row[1] for row in db.execute('PRAGMA table_info(requests)')}
            if 'origin' not in columns:
                db.execute("ALTER TABLE requests ADD COLUMN origin TEXT NOT NULL DEFAULT 'google'")
                db.execute("UPDATE requests SET origin='demo' WHERE EXISTS (SELECT 1 FROM receipts WHERE event_id LIKE 'demo-mail:' || requests.ref)")
                db.execute("UPDATE requests SET origin='sample' WHERE ref='SUP-CLASS001' AND EXISTS (SELECT 1 FROM receipts WHERE event_id='sample-email-001')")
            db.execute("INSERT OR IGNORE INTO request_details SELECT r.ref,coalesce((SELECT min(a.at) FROM activity a WHERE a.ref=r.ref AND a.source='gmail'),r.updated_at),'first_observed_fallback' FROM requests r")
            # Backfill old activity exactly once; IDs make migration/reconnect repeatable.
            for row in db.execute('SELECT * FROM activity ORDER BY seq').fetchall():
                self._notification(db, row, historical=True)

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def checkpoint(self, key, value=None):
        with self.connect() as db:
            if value is not None:
                db.execute('INSERT OR REPLACE INTO checkpoints VALUES (?,?)', (key, value))
            row = db.execute('SELECT value FROM checkpoints WHERE key=?', (key,)).fetchone()
            return row[0] if row else None

    def calendar_ref(self, event_id):
        with self.connect() as db:
            row = db.execute('SELECT ref FROM calendar_events WHERE id=?', (event_id,)).fetchone()
            return row[0] if row else None

    def calendar_version(self, event_id):
        with self.connect() as db:
            row = db.execute('SELECT version FROM calendar_events WHERE id=?', (event_id,)).fetchone()
            return row[0] if row else None

    def snapshot(self):
        with self.connect() as db:
            # A read transaction keeps lists/counts/cursor from different commits from mixing.
            db.execute('BEGIN')
            rows = [dict(r) for r in db.execute('SELECT * FROM requests ORDER BY updated_at DESC,ref')]
            activity = [dict(r) for r in db.execute('SELECT * FROM activity ORDER BY seq DESC LIMIT 80')]
            counts = {s: sum(r['status'] == s for r in rows) for s in
                      ['new', 'in_progress', 'scheduled', 'needs_follow_up', 'resolved']}
            chat = self._messages(db)
            return dict(requests=rows, activity=activity, counts=counts, chat=chat,
                        cursor=activity[0]['seq'] if activity else 0)

    def apply(self, e):
        """Deduplication and all business changes commit before the caller broadcasts."""
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            # Upgrade an observed-time fallback only with authenticated Gmail internalDate.
            if e.get('trusted_google') and e.get('received_at'):
                db.execute("UPDATE request_details SET received_at=?,received_basis='gmail_internal_date' WHERE ref=? AND received_basis='first_observed_fallback'", (e['received_at'], e['ref']))
            if db.execute('SELECT 1 FROM receipts WHERE source=? AND event_id=?',
                          (e['source'], e['event_id'])).fetchone():
                return False
            ref, source = e['ref'], e['source']
            at = now()
            if source == 'gmail':
                created = db.execute('INSERT OR IGNORE INTO requests(ref,title,status,session_at,updated_at,origin) VALUES (?,?,?,NULL,?,?)',
                           (ref, e['title'], 'new', at, 'demo' if e['event_id'].startswith('demo-') else 'sample' if e['event_id'].startswith('sample-') else 'google')).rowcount
                db.execute('INSERT OR IGNORE INTO request_details VALUES (?,?,?)',
                           (ref, e.get('received_at') or at, 'gmail_internal_date' if e.get('trusted_google') and e.get('received_at') else 'first_observed_fallback'))
                message = 'Support email received'
                # A Calendar event may arrive before its email; reconcile the latest saved event.
                calendar = db.execute('SELECT * FROM calendar_events WHERE ref=? ORDER BY version DESC,id DESC LIMIT 1', (ref,)).fetchone()
                if calendar and created:
                    db.execute('UPDATE requests SET status=?,session_at=?,updated_at=? WHERE ref=?',
                               ('needs_follow_up' if calendar['cancelled'] else 'scheduled',
                                None if calendar['cancelled'] else calendar['start'], at, ref))
                    message += ' · saved tutoring change matched'
            elif source == 'calendar':
                previous = db.execute('SELECT * FROM calendar_events WHERE id=?', (e['calendar_id'],)).fetchone()
                if previous and previous['ref'] != ref:
                    raise ValueError('A tutoring event reference is immutable; cancel it and create a new event.')
                if previous and e['version'] <= previous['version']:
                    message = 'Older tutoring change ignored'
                else:
                    db.execute('INSERT OR REPLACE INTO calendar_events VALUES (?,?,?,?,?)',
                               (e['calendar_id'], ref, e['version'], e['cancelled'], e.get('start')))
                    latest = db.execute('SELECT id FROM calendar_events WHERE ref=? ORDER BY version DESC,id DESC LIMIT 1', (ref,)).fetchone()
                    if latest['id'] == e['calendar_id']:
                        db.execute('UPDATE requests SET status=?,session_at=?,updated_at=? WHERE ref=?',
                                   ('needs_follow_up' if e['cancelled'] else 'scheduled',
                                    None if e['cancelled'] else e.get('start'), at, ref))
                    exists = db.execute('SELECT 1 FROM requests WHERE ref=?', (ref,)).fetchone()
                    message = ('Tutoring cancelled' if e['cancelled'] else 'Tutoring scheduled / updated')
                    if not exists:
                        message += ' · waiting for matching email'
            else:
                changed = db.execute('UPDATE requests SET status=?,updated_at=? WHERE ref=?',
                                     (e['status'], at, ref)).rowcount
                if not changed:
                    raise KeyError(ref)
                message = 'Teacher set status: ' + e['status'].replace('_', ' ')
            db.execute('INSERT INTO receipts VALUES (?,?)', (source, e['event_id']))
            cursor = db.execute('INSERT INTO activity(ref,source,message,at) VALUES (?,?,?,?)',
                       (ref, source, message, at))
            row = db.execute('SELECT * FROM activity WHERE seq=?', (cursor.lastrowid,)).fetchone()
            self._notification(db, row)
            if source == 'gmail' and created and e.get('trusted_google') and e.get('received_at'):
                config_row = db.execute("SELECT value FROM checkpoints WHERE key='automation_config'").fetchone()
                config = json.loads(config_row[0]) if config_row else {}
                request = db.execute('SELECT status FROM requests WHERE ref=?', (ref,)).fetchone()
                if config.get('enabled') and e['received_at'] >= config['activated_at'] and request['status'] == 'new':
                    import hashlib, os
                    event_id = hashlib.sha256(('bia-support-v1:' + config['account_hash'] + ':' + e['event_id']).encode()).hexdigest()
                    db.execute('INSERT OR IGNORE INTO support_jobs(ref,message_id,calendar_id,event_id,rfc_id,stage,updated_at) VALUES (?,?,?,?,?,?,?)',
                               (ref, e['event_id'], os.getenv('GOOGLE_CALENDAR_ID', 'primary'), event_id,
                                '<bia-' + event_id + '@classroom.local>', 'queued', at))
                    self._job_notice(db, ref, 'New request queued for a scheduling proposal. No invitation or email has been sent.')
        return True

    @staticmethod
    def _decode(row):
        message = dict(row)
        message['metadata'] = json.loads(message['metadata'])
        return message

    def _messages(self, db):
        return [self._decode(r) for r in db.execute(
            'SELECT * FROM (SELECT * FROM chat_messages ORDER BY seq DESC LIMIT 200) ORDER BY seq')]

    def messages(self):
        with self.connect() as db:
            return self._messages(db)

    def _notification(self, db, activity, historical=False):
        request = db.execute('SELECT * FROM requests WHERE ref=?', (activity['ref'],)).fetchone()
        meta = dict(source=activity['source'], ref=activity['ref'], activity_seq=activity['seq'])
        job = db.execute('SELECT stage,start,end,revision FROM support_jobs WHERE ref=?', (activity['ref'],)).fetchone()
        if job:
            meta.update(workflow_stage=job['stage'], proposal_start=job['start'], proposal_end=job['end'], proposal_revision=job['revision'])
        text = activity['message'] + ' · ' + activity['ref']
        if request:
            meta.update(origin=request['origin'])
            if not historical:
                meta.update(session_at=request['session_at'], status=request['status'])
            text += '\n' + request['title']
            if not historical:
                text += '\nSaved status: ' + request['status'].replace('_', ' ') + '.'
        db.execute("INSERT OR IGNORE INTO chat_messages(id,role,content,state,metadata,at) VALUES (?,?,?,?,?,?)",
                   ('event:' + str(activity['seq']), 'notification', text, 'complete', json.dumps(meta), activity['at']))

    def begin_reply(self, request_id, question, metadata):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            existing = db.execute('SELECT * FROM chat_messages WHERE id=?', ('assistant:' + request_id,)).fetchone()
            if existing:
                return self._decode(existing), False
            at = now()
            for role, content, state in [('user', question, 'complete'), ('assistant', '', 'streaming')]:
                db.execute('INSERT INTO chat_messages(id,role,content,state,metadata,at) VALUES (?,?,?,?,?,?)',
                           (role + ':' + request_id, role, content, state, json.dumps(metadata), at))
            row = db.execute('SELECT * FROM chat_messages WHERE id=?', ('assistant:' + request_id,)).fetchone()
            return self._decode(row), True

    def update_reply(self, message_id, delta='', state=None, error=None):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM chat_messages WHERE id=?', (message_id,)).fetchone()
            meta = json.loads(row['metadata'])
            if error:
                meta['error'] = error
            db.execute('UPDATE chat_messages SET content=content || ?,state=?,metadata=?,revision=revision+1 WHERE id=?',
                       (delta, state or row['state'], json.dumps(meta), message_id))
            return self._decode(db.execute('SELECT * FROM chat_messages WHERE id=?', (message_id,)).fetchone())

    def interrupt_replies(self):
        with self.connect() as db:
            db.execute("UPDATE chat_messages SET state='interrupted',revision=revision+1 WHERE state='streaming'")

    def job(self, ref):
        with self.connect() as db:
            row = db.execute('SELECT * FROM support_jobs WHERE ref=?', (ref,)).fetchone()
            return dict(row) if row else None

    def public_jobs(self):
        with self.connect() as db:
            return [dict(row) for row in db.execute('SELECT ref,stage,start,end,error,revision,updated_at,simulation FROM support_jobs ORDER BY updated_at DESC')]

    def next_job(self):
        with self.connect() as db:
            row = db.execute("SELECT * FROM support_jobs WHERE stage NOT IN ('awaiting_approval','acknowledged','failed') AND (retry_at IS NULL OR retry_at<=?) ORDER BY updated_at LIMIT 1", (now(),)).fetchone()
            return dict(row) if row else None

    def _job_notice(self, db, ref, message):
        cursor = db.execute('INSERT INTO activity(ref,source,message,at) VALUES (?,?,?,?)', (ref, 'automation', message, now()))
        row = db.execute('SELECT * FROM activity WHERE seq=?', (cursor.lastrowid,)).fetchone()
        self._notification(db, row)

    def job_update(self, ref, stage, message=None, **fields):
        allowed = {'start','end','recipient','thread_id','parent_id','reply_subject','references','sent_id','error','attempts','retry_at','booking_attempted'}
        if not set(fields) <= allowed:
            raise ValueError('Unknown workflow field')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            current = dict(db.execute('SELECT * FROM support_jobs WHERE ref=?', (ref,)).fetchone())
            changed = current['stage'] != stage or any(current[k] != v for k,v in fields.items())
            if not changed and not message:
                return
            values = {'stage': stage, 'updated_at': now(), **fields}
            db.execute('UPDATE support_jobs SET ' + ','.join('"' + k + '"=?' for k in values) + ',revision=revision+1 WHERE ref=?', [*values.values(), ref])
            if stage == 'booked' and (fields.get('start') or current['start']):
                db.execute("UPDATE requests SET status='scheduled',session_at=?,updated_at=? WHERE ref=?", (fields.get('start') or current['start'], now(), ref))
            if message:
                self._job_notice(db, ref, message)
        if self.workflow_notifier:
            self.workflow_notifier()

    def approve_job(self, ref, revision):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute("SELECT * FROM support_jobs WHERE ref=? AND stage='awaiting_approval' AND revision=?", (ref, revision)).fetchone()
            if not row:
                raise ValueError('That proposal changed or is no longer awaiting approval. Review its latest time.')
            db.execute("UPDATE support_jobs SET stage='approved',revision=revision+1,updated_at=? WHERE ref=?", (now(), ref))
            self._job_notice(db, ref, 'You approved this proposal. Rechecking availability before booking and sending the confirmation.')
        if self.workflow_notifier:
            self.workflow_notifier()
