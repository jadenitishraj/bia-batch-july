"""Local tables and guest rendering: identities/subjects in tables never enter Gemini."""
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def window_seconds(text):
    lower = text.lower()
    if re.search(r'last\s+(?:half(?: an?)?\s+hour|30\s*(?:min|minute)s?)', lower): return 1800
    if re.search(r'last\s+(?:an?\s+)?hour\b', lower): return 3600
    match = re.search(r'last\s+(\d+)\s*(minutes?|mins?|hours?|hrs?)\b', lower)
    if match:
        return min(int(match[1]) * (3600 if match[2].startswith(('hour','hr')) else 60), 366 * 86400)
    return None


def requested(text):
    lower = text.lower()
    return bool(window_seconds(text) or re.search(r'\b(table|list|show|which|upcoming)\b.*\b(requests?|jobs?|meetings?|sessions?)\b|\bjobs?\b.*\b(queued|progress|booked|acknowledged|failed|approval)\b', lower))


def stage_filter(text):
    lower = text.lower()
    for pattern, values in [
        (r'\bin progress\b', ['preparing','approved','booking','acknowledging']),
        (r'\bqueued\b', ['queued']), (r'awaiting approval|pending proposal', ['awaiting_approval']),
        (r'\backnowledged\b', ['acknowledged']), (r'\bbooked\b', ['booked','acknowledging','acknowledged','send_uncertain']),
        (r'\bfailed\b', ['failed','retry_wait','send_uncertain','booking_uncertain'])]:
        if re.search(pattern, lower): return values
    return []


def query_rows(store, text, current=None):
    current = current or datetime.now(timezone.utc)
    seconds = window_seconds(text)
    clauses, params = ['1'], []
    if seconds is not None:
        clauses += ['d.received_at>=?', 'd.received_at<=?']
        params += [(current-timedelta(seconds=seconds)).isoformat(), current.isoformat()]
    stages = stage_filter(text)
    if re.search(r'\bin progress\b',text.lower()) and 'job' not in text.lower():
        stages=[];clauses.append("r.status='in_progress'")
    if re.search(r'\b(waiting|pending)\b',text.lower()) and not re.search(r'pending proposal|awaiting approval',text.lower()):
        clauses.append("r.status IN ('new','in_progress','needs_follow_up')")
    if stages:
        clauses.append('j.stage IN (' + ','.join('?' for _ in stages) + ')'); params.extend(stages)
    if re.search(r'\bnew\b', text.lower()): clauses.append("r.status='new'")
    if re.search(r'\bresolved\b', text.lower()): clauses.append("r.status='resolved'")
    if re.search(r'\bscheduled\b', text.lower()): clauses.append("r.status='scheduled'")
    if re.search(r'\bupcoming\b', text.lower()):
        clauses += ["r.status='scheduled'", 'julianday(r.session_at)>=julianday(?)']; params.append(current.isoformat())
    refs = re.findall(r'\bSUP-[A-Z0-9-]{3,48}\b', text.upper())
    if refs:
        clauses.append('r.ref IN (' + ','.join('?' for _ in refs) + ')'); params.extend(refs)
    if re.search(r'\b(real|google|gmail)\b', text.lower()): clauses.append("r.origin='google'")
    elif re.search(r'\bdemo\b', text.lower()): clauses.append("r.origin='demo'")
    elif re.search(r'\bsample\b', text.lower()): clauses.append("r.origin='sample'")
    # Ordinary report grammar is not a subject filter. Keep explicit lesson/topic words.
    topic_text = re.sub(r'last\s+(?:(?:half(?: an?)?\s+|an?\s+)?hour|\d+\s*(?:minutes?|mins?|hours?|hrs?))', '', text.lower())
    stop = set('show list table all tracked requests request jobs job which are is the upcoming meetings meeting please with corresponding and from in progress queued booked acknowledged failed real google gmail calendar demo sample pending proposals proposal awaiting approval support sessions session my received over past of to for a an have got me give needs follow up new resolved scheduled status'.split())
    if not refs:
        terms = list(dict.fromkeys(word for word in re.findall(r'[a-z0-9]+', topic_text) if len(word)>2 and word not in stop and not word.isdigit()))
        for term in terms[:6]:
            clauses.append('lower(r.title) LIKE ?');params.append('%'+term+'%')
    with store.connect() as db:
        rows = [dict(r) for r in db.execute('''SELECT r.ref,r.title,d.received_at,d.received_basis,r.status,r.origin,
                 coalesce(j.stage,'tracked_only') AS workflow_stage,r.session_at,j.start AS proposal_at,j.error
                 FROM requests r LEFT JOIN request_details d ON d.ref=r.ref LEFT JOIN support_jobs j ON j.ref=r.ref
                 WHERE ''' + ' AND '.join(clauses) + ' ORDER BY d.received_at DESC,r.ref', params)]
    return rows, dict(captured_at=current.isoformat(), window_seconds=seconds,
                      window_start=(current-timedelta(seconds=seconds)).isoformat() if seconds is not None else None,
                      window_end=current.isoformat(), stages=stages,
                      fallback_rows=sum(r['received_basis'] != 'gmail_internal_date' for r in rows))


def make_report(store, text, current=None):
    rows, scope = query_rows(store, text, current)
    report_id = str(uuid.uuid4())
    payload = dict(rows=rows, total=len(rows), scope=scope)
    with store.connect() as db:
        db.execute('INSERT INTO report_snapshots VALUES (?,?)', (report_id, json.dumps(payload)))
    local = dict(type='requests', report_id=report_id, rows=rows[:20], total=len(rows), scope=scope)
    # The model sees aggregate state, not the subjects, guest identities or table rows.
    context = dict(kind='classroom', intent='local_report', captured_at=scope['captured_at'], total_matching=len(rows), records=[],
                   local_table=True, displayed_rows=min(20,len(rows)), scope=scope,
                   aggregate={'total':len(rows), 'by_origin':{o:sum(r['origin']==o for r in rows) for o in ['google','demo','sample']}, 'exact':True})
    return context, local


def page(store, report_id, offset):
    with store.connect() as db:
        row = db.execute('SELECT payload FROM report_snapshots WHERE id=?', (report_id,)).fetchone()
    if not row: raise KeyError(report_id)
    payload=json.loads(row[0])
    return dict(rows=payload['rows'][offset:offset+20], total=payload['total'], scope=payload['scope'])


def count_window_clause(text):
    seconds = window_seconds(text)
    if seconds is None: return None
    current = datetime.now(timezone.utc)
    return ((current-timedelta(seconds=seconds)).isoformat(),current.isoformat())
