from datetime import datetime,timedelta,timezone
from backend import reporting,chat
from backend.store import Store


def test_receive_windows_original_time_fallback_and_stable_pagination(tmp_path):
    store=Store(tmp_path/'reports.sqlite3')
    clock=datetime(2026,11,22,4,0,tzinfo=timezone.utc)
    for n in range(25):
        received=clock-timedelta(minutes=n)
        store.apply(dict(source='gmail',event_id=f'real:{n}',ref=f'SUP-TIME{n:03d}',title='Private subject',trusted_google=True,received_at=received.isoformat()))
    # A status update now must not make an older email newly received.
    store.apply(dict(source='teacher',event_id='late-update',ref='SUP-TIME024',status='resolved'))
    rows,scope=reporting.query_rows(store,'Table of requests from the last 20 minutes',clock)
    assert len(rows)==21  # Inclusive exact lower boundary.
    assert 'SUP-TIME024' not in {r['ref'] for r in rows}
    assert all(r['received_basis']=='gmail_internal_date' for r in rows)
    assert reporting.window_seconds('last half hour')==1800
    assert reporting.window_seconds('last hour')==3600
    context,local=reporting.make_report(store,'Show requests from the last half hour',clock)
    assert context['total_matching']==25 and context['records']==[]
    assert 'Private subject' not in str(context)
    assert len(local['rows'])==20
    more=reporting.page(store,local['report_id'],20)
    assert len(more['rows'])==5
    assert len({r['ref'] for r in local['rows']+more['rows']})==25
    received_before=rows[0]['received_at']
    store.apply(dict(source='gmail',event_id='real:0',ref='SUP-TIME000',title='Not reapplied',trusted_google=True,received_at=(clock+timedelta(days=1)).isoformat()))
    assert reporting.query_rows(store,'Show requests',clock)[0][0]['received_at']==received_before


def test_workflow_filters_and_upcoming_meetings(tmp_path):
    store=Store(tmp_path/'stages.sqlite3')
    store.checkpoint('automation_config','{"enabled":true,"activated_at":"2026-11-22T02:00:00+00:00","account_hash":"test"}')
    store.apply(dict(source='gmail',event_id='real-queued',ref='SUP-QUEUED',title='Synthetic',trusted_google=True,received_at='2026-11-22T03:00:00+00:00'))
    rows,_=reporting.query_rows(store,'Which jobs are queued?')
    assert [r['ref'] for r in rows]==['SUP-QUEUED']
    store.job_update('SUP-QUEUED','awaiting_approval',None,start='2026-11-23T10:00:00+05:30',end='2026-11-23T10:30:00+05:30')
    rows,_=reporting.query_rows(store,'Show jobs awaiting approval')
    assert len(rows)==1 and rows[0]['session_at'] is None
    store.job_update('SUP-QUEUED','booked',None,start='2026-11-23T10:00:00+05:30')
    rows,_=reporting.query_rows(store,'List upcoming support meetings',datetime(2026,11,22,tzinfo=timezone.utc))
    assert len(rows)==1
    rows,_=reporting.query_rows(store,'List upcoming support meetings',datetime(2026,11,24,tzinfo=timezone.utc))
    assert rows==[]


def test_table_and_guest_chat_routes_keep_local_details_out_of_gemini(tmp_path,monkeypatch):
    import importlib,json,uuid
    from fastapi.testclient import TestClient
    from backend import main,google_sync,automation
    monkeypatch.setenv('DATABASE_PATH',str(tmp_path/'routes.sqlite3'))
    monkeypatch.setenv('GOOGLE_TOKEN_FILE',str(tmp_path/'no-token'))
    main=importlib.reload(main)
    monkeypatch.setattr(chat,'configuration',lambda:('test-key','test-model'))
    observed=[]
    async def fake_stream(question,history,context):
        observed.append(context)
        yield 'The authoritative details are shown locally below.'
    monkeypatch.setattr(chat,'stream_reply',fake_stream)
    class Call:
        def execute(self):return {'attendees':[{'email':'explicit-guest@example.test','responseStatus':'accepted'}],'status':'confirmed'}
    class Calendar:
        def events(self):return self
        def get(self,**kw):
            assert kw['calendarId']=='primary' and kw['eventId']=='tracked-event'
            return Call()
    monkeypatch.setattr(automation,'load_credentials',lambda path:object())
    monkeypatch.setattr(google_sync,'build',lambda *a,**kw:Calendar())
    with TestClient(main.app) as client:
        client.post('/api/events',json={'source':'gmail','event_id':'sample-route','ref':'SUP-ROUTE001','title':'Private local-only subject'})
        client.post('/api/events',json={'source':'calendar','event_id':'sample-calendar','ref':'SUP-ROUTE001','calendar_id':'primary:tracked-event','version':'2026-11-22T04:00:00Z','start':'2026-11-23T04:00:00Z','cancelled':False})
        response=client.post('/api/chat',json={'message':'Show a table of all tracked requests from the last 20 minutes','request_id':str(uuid.uuid4())})
        assert response.status_code==200
        packets=[json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
        report=packets[-1]['message']['metadata']['local_report']
        assert report['total']==1 and report['rows'][0]['title']=='Private local-only subject'
        assert 'Private local-only' not in json.dumps(observed[-1])
        response=client.post('/api/chat',json={'message':'Who all are invited to SUP-ROUTE001?','request_id':str(uuid.uuid4())})
        assert response.status_code==200
        packets=[json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
        assert packets[-1]['message']['metadata']['local_report']=={'type':'guests','ref':'SUP-ROUTE001'}
        guests=client.get('/api/requests/SUP-ROUTE001/guests').json()
        assert guests['guests'][0]['email']=='explicit-guest@example.test'
        assert 'explicit-guest' not in json.dumps(observed)
        assert 'explicit-guest' not in json.dumps(main.store.messages())
