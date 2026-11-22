import json
from datetime import datetime,timedelta,timezone
from types import SimpleNamespace
import pytest
from googleapiclient.errors import HttpError
from backend import automation
from backend.store import Store

CURRENT=datetime(2026,11,22,4,0,tzinfo=timezone.utc)  # Sunday, 09:30 IST: no weekday restriction.

class Call:
    def __init__(self, call): self.call=call
    def execute(self): return self.call()

def missing():
    raise HttpError(SimpleNamespace(status=404,reason='Not found'),b'{}')

class FakeGoogle:
    def __init__(self):
        self.created={};self.inserts=0;self.sends=0;self.sent=[];self.busy=[]
        self.insert_timeout=False;self.send_timeout=False;self.crash_send=False;self.freebusy_error=False
    def getProfile(self,**kw): return Call(lambda:{'emailAddress':'teacher@example.test'})
    def users(self): return self
    def messages(self): return self
    def events(self): return self
    def freebusy(self): return self
    def query(self,body):
        def run():
            if self.freebusy_error: return {'calendars':{'primary':{'errors':[{'reason':'forbidden'}]}}}
            return {'calendars':{v['id']:{'busy':[{'start':a.isoformat(),'end':b.isoformat()} for a,b in self.busy]} for v in body['items']}}
        return Call(run)
    def get(self,**kw):
        if 'eventId' in kw:
            return Call(lambda:self.created[kw['eventId']] if kw['eventId'] in self.created else missing())
        return Call(lambda:{'threadId':'thread-one','payload':{'headers':[
            {'name':'Subject','value':'[SUP-NEW001] Help'}, {'name':'From','value':'Student <student@example.test>'},
            {'name':'Message-ID','value':'<original@example.test>'}]}})
    def insert(self,calendarId,body,sendUpdates):
        def run():
            assert sendUpdates=='all'
            assert body['attendees']==[{'email':'student@example.test'}]
            self.inserts+=1;self.created[body['id']]=body
            if self.insert_timeout: raise TimeoutError('lost response')
            return body
        return Call(run)
    def list(self,**kw): return Call(lambda:{'messages':[{'id':i} for i in self.sent]})
    def send(self,userId,body):
        def run():
            self.sends+=1
            assert body['threadId']=='thread-one'
            if self.crash_send:
                self.sent.append('sent-one');raise SystemExit('process died after send')
            if self.send_timeout: raise TimeoutError('unknown send outcome')
            self.sent.append('sent-one');return {'id':'sent-one'}
        return Call(run)


def prepared(tmp_path, enabled=True):
    store=Store(tmp_path/'workflow.sqlite3')
    store.checkpoint('automation_config',json.dumps({'enabled':enabled,'activated_at':'2026-11-22T03:00:00+00:00','account_hash':'test'}))
    store.apply(dict(source='gmail',event_id='real-new',ref='SUP-NEW001',title='Synthetic request',trusted_google=True,received_at='2026-11-22T03:30:00+00:00'))
    return store


def test_proposal_only_until_specific_approval_then_no_duplicate_writes(tmp_path):
    store=prepared(tmp_path);google=FakeGoogle()
    assert store.job('SUP-NEW001')['stage']=='queued'
    automation.run_one(store,google,google,CURRENT)
    proposal=store.job('SUP-NEW001')
    assert proposal['stage']=='awaiting_approval'
    assert google.inserts==google.sends==0
    assert not automation.run_one(store,google,google,CURRENT)
    store.approve_job('SUP-NEW001',proposal['revision'])
    with pytest.raises(ValueError):store.approve_job('SUP-NEW001',proposal['revision'])
    automation.run_one(store,google,google,CURRENT)
    assert store.job('SUP-NEW001')['stage']=='acknowledged'
    assert google.inserts==google.sends==1
    restarted=Store(store.path)
    assert not automation.run_one(restarted,google,google,CURRENT)
    assert google.inserts==google.sends==1
    assert all('student@example.test' not in m['content'] for m in store.messages())
    assert [m['metadata'].get('workflow_stage') for m in store.messages() if m['metadata'].get('source')=='automation'][-1]=='acknowledged'


def test_no_backfill_for_existing_or_older_or_disabled_requests(tmp_path):
    store=prepared(tmp_path,False)
    assert store.job('SUP-NEW001') is None
    store.checkpoint('automation_config',json.dumps({'enabled':True,'activated_at':'2026-11-22T03:00:00+00:00','account_hash':'test'}))
    store.apply(dict(source='gmail',event_id='another-mail-same-ref',ref='SUP-NEW001',title='Existing',trusted_google=True,received_at='2026-11-22T04:00:00+00:00'))
    store.apply(dict(source='gmail',event_id='old-mail',ref='SUP-OLD001',title='Older email',trusted_google=True,received_at='2026-11-21T04:00:00+00:00'))
    assert store.public_jobs()==[]


def test_approval_revalidation_busy_slot_requires_fresh_approval(tmp_path):
    store=prepared(tmp_path);google=FakeGoogle()
    automation.run_one(store,google,google,CURRENT)
    proposal=store.job('SUP-NEW001');store.approve_job(proposal['ref'],proposal['revision'])
    start=datetime.fromisoformat(proposal['start']);google.busy=[(start,start+timedelta(hours=1))]
    automation.run_one(store,google,google,CURRENT)
    replacement=store.job(proposal['ref'])
    assert replacement['stage']=='awaiting_approval'
    assert datetime.fromisoformat(replacement['start'])>=start+timedelta(hours=1)
    assert google.inserts==google.sends==0
    with pytest.raises(ValueError):store.approve_job(proposal['ref'],proposal['revision'])


def test_calendar_timeout_reconciles_same_event_and_crash_after_send_is_not_resent(tmp_path):
    store=prepared(tmp_path);google=FakeGoogle();google.insert_timeout=True;google.crash_send=True
    automation.run_one(store,google,google,CURRENT)
    proposal=store.job('SUP-NEW001');store.approve_job(proposal['ref'],proposal['revision'])
    with pytest.raises(SystemExit):automation.run_one(store,google,google,CURRENT)
    assert store.job('SUP-NEW001')['stage']=='acknowledging'
    restarted=Store(store.path)
    automation.run_one(restarted,google,google,CURRENT)
    assert restarted.job('SUP-NEW001')['stage']=='acknowledged'
    assert google.inserts==google.sends==1


def test_ambiguous_gmail_send_never_blindly_resends(tmp_path):
    store=prepared(tmp_path);google=FakeGoogle();google.send_timeout=True
    automation.run_one(store,google,google,CURRENT)
    proposal=store.job('SUP-NEW001');store.approve_job(proposal['ref'],proposal['revision'])
    automation.run_one(store,google,google,CURRENT)
    assert store.job('SUP-NEW001')['stage']=='send_uncertain'
    store.job_update(proposal['ref'],'send_uncertain',None,retry_at=None)
    automation.run_one(Store(store.path),google,google,CURRENT)
    assert google.sends==1
    assert store.job('SUP-NEW001')['stage']=='send_uncertain'


def test_free_alternate_only_replaces_proposal_and_busy_alternate_keeps_it(tmp_path):
    store=prepared(tmp_path);google=FakeGoogle()
    automation.run_one(store,google,google,CURRENT)
    proposal=store.job('SUP-NEW001')
    automation.propose_alternative(store,proposal['ref'],proposal['revision'],'Is tomorrow at 4 p.m. free instead?',google,CURRENT)
    revised=store.job(proposal['ref'])
    assert datetime.fromisoformat(revised['start']).astimezone(automation.ZONE).hour==16
    assert revised['stage']=='awaiting_approval'
    assert google.inserts==google.sends==0
    start=datetime.fromisoformat(revised['start']);google.busy=[(start,start+timedelta(minutes=30))]
    automation.propose_alternative(store,revised['ref'],revised['revision'],'Check 4 pm instead',google,CURRENT)
    assert store.job(revised['ref'])['start']==revised['start']
    assert google.inserts==google.sends==0
    with pytest.raises(ValueError):automation.alternative_time('Check 4 instead',revised,CURRENT)
    with pytest.raises(ValueError):automation.alternative_time('Check tomorrow 5 pm instead',revised,CURRENT)
    with pytest.raises(ValueError):automation.alternative_time('Check 4 pm UTC instead',revised,CURRENT)
    with pytest.raises(ValueError):automation.alternative_time('Check 3 pm or 4 pm instead',revised,CURRENT)


def test_business_window_busy_failures_and_multiple_proposals(tmp_path):
    saturday=datetime(2026,11,21,11,20,tzinfo=timezone.utc) # 16:50 IST
    start,end=automation.next_slot(saturday,[])
    assert start.day==22 and start.hour==9 and end.hour==9 and end.minute==30
    store=prepared(tmp_path);google=FakeGoogle();google.freebusy_error=True
    automation.run_one(store,google,google,CURRENT)
    assert store.job('SUP-NEW001')['stage']=='retry_wait'
    assert google.inserts==google.sends==0


def test_safe_proposal_demo_never_uses_google_even_when_approved(tmp_path,monkeypatch):
    store=Store(tmp_path/'simulation.sqlite3')
    monkeypatch.setattr(automation,'services',lambda:(_ for _ in ()).throw(AssertionError('No Google calls allowed')))
    ref=automation.prepare_simulation(store)
    proposal=store.job(ref)
    assert proposal['simulation']==1 and proposal['stage']=='awaiting_approval'
    assert not automation.run_one(store)
    store.approve_job(ref,proposal['revision'])
    assert automation.run_one(store)
    assert store.job(ref)['stage']=='acknowledged'
    assert store.job(ref)['sent_id']=='simulation-only'


def test_later_acknowledgment_does_not_undo_calendar_cancellation(tmp_path):
    store=prepared(tmp_path);google=FakeGoogle()
    automation.run_one(store,google,google,CURRENT)
    proposal=store.job('SUP-NEW001');store.approve_job(proposal['ref'],proposal['revision'])
    automation.run_one(store,google,google,CURRENT)
    store.apply(dict(source='calendar',event_id='cancel-after-booking',ref='SUP-NEW001',calendar_id='primary:'+proposal['event_id'],version='2026-11-22T05:00:00+00:00',cancelled=True,start=None))
    store.job_update('SUP-NEW001','acknowledged','Confirmation receipt reconciled.')
    request=store.snapshot()['requests'][0]
    assert request['status']=='needs_follow_up' and request['session_at'] is None


def test_natural_time_selection_and_ambiguous_approval_never_book(tmp_path,monkeypatch):
    import importlib,uuid
    from fastapi.testclient import TestClient
    from backend import main,chat
    monkeypatch.setenv('DATABASE_PATH',str(tmp_path/'actions.sqlite3'))
    monkeypatch.setenv('GOOGLE_TOKEN_FILE',str(tmp_path/'no-google'))
    main=importlib.reload(main)
    monkeypatch.setattr(chat,'configuration',lambda:(None,'no-model'))
    monkeypatch.setattr(automation,'services',lambda:(_ for _ in ()).throw(AssertionError('No live services in simulation')))
    def ask(client,text):
        ids=[m['id'] for m in client.get('/api/snapshot').json()['chat']]
        response=client.post('/api/chat',json={'message':text,'request_id':str(uuid.uuid4()),'context_message_ids':ids})
        assert response.status_code==200
        packets=[json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
        return packets[-1]['message']
    with TestClient(main.app) as client:
        first=client.post('/api/automation/demo').json()['ref']
        answer=ask(client,'okay, go ahead and set up the meeting for tomorrow at 4 pm')
        assert main.store.job(first)['stage']=='awaiting_approval'
        assert answer['metadata']['local_action']
        unclear=ask(client,'Is tomorrow afternoon free instead?')
        assert 'time' in unclear['content'].lower() and main.store.job(first)['stage']=='awaiting_approval'
        second=client.post('/api/automation/demo').json()['ref']
        answer=ask(client,'okay, go ahead and set up the meeting')
        assert 'identify' in answer['content'].lower()
        assert main.store.job(first)['stage']==main.store.job(second)['stage']=='awaiting_approval'
        revision=main.store.job(first)['revision']
        assert client.post('/api/proposals/'+first+'/approve',json={'revision':revision}).status_code==200
        assert client.post('/api/proposals/'+first+'/approve',json={'revision':revision}).status_code==409


def test_preparing_transition_reaches_websocket_while_availability_is_pending(tmp_path,monkeypatch):
    import importlib,hashlib,threading
    from fastapi.testclient import TestClient
    from backend import main
    seeded=prepared(tmp_path)
    config={'enabled':False,'activated_at':'2026-11-22T03:00:00+00:00','account_hash':hashlib.sha256(b'teacher@example.test').hexdigest()}
    seeded.checkpoint('automation_config',json.dumps(config))
    monkeypatch.setenv('DATABASE_PATH',seeded.path)
    monkeypatch.setenv('GOOGLE_TOKEN_FILE',str(tmp_path/'no-reader'))
    main=importlib.reload(main)
    release=threading.Event()
    google=FakeGoogle()
    original=google.query
    def delayed_query(body):
        def run():
            release.wait(5)
            return original(body).execute()
        return Call(run)
    google.query=delayed_query
    monkeypatch.setattr(automation,'services',lambda:(google,google))
    try:
        with TestClient(main.app) as client:
            with client.websocket_connect('/ws') as ws:
                ws.receive_json()
                config['enabled']=True;main.store.checkpoint('automation_config',json.dumps(config))
                while True:
                    update=ws.receive_json()
                    if update['jobs'][0]['stage']!='queued':break
                assert update['jobs'][0]['stage']=='preparing'
                assert not release.is_set()
                assert google.inserts==google.sends==0
                release.set()
    finally:
        release.set()
