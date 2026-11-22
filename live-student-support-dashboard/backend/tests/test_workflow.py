import importlib
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from backend.store import Store


def email(ref='SUP-CLASS001', event_id='mail-1'):
    return dict(source='gmail', ref=ref, event_id=event_id, title='[SUP-CLASS001] Python help')


def calendar(cancelled=False, version='2026-11-22T10:00:00+00:00', event_id='cal-1'):
    return dict(source='calendar', event_id=event_id, ref='SUP-CLASS001', calendar_id='lesson-1',
                version=version, cancelled=cancelled, start='2026-11-23T10:00:00+00:00')


def test_atomic_receipts_out_of_order_and_restart(tmp_path):
    path = tmp_path / 'test.sqlite3'
    store = Store(path)
    assert store.apply(calendar())
    assert store.snapshot()['requests'] == []
    assert store.apply(email())
    assert store.snapshot()['requests'][0]['status'] == 'scheduled'
    assert not store.apply(email())
    assert not store.apply(calendar())
    store.apply(calendar(True, '2026-11-22T11:00:00+00:00', 'cancel-1'))
    store.apply(calendar(False, '2026-11-22T09:00:00+00:00', 'stale-1'))
    restored = Store(path).snapshot()
    assert restored['requests'][0]['status'] == 'needs_follow_up'
    assert restored['requests'][0]['session_at'] is None
    assert restored['cursor'] == 4
    assert restored['activity'][0]['message'] == 'Older tutoring change ignored'
    store.apply(dict(source='teacher', ref='SUP-CLASS001', event_id='resolve-1', status='resolved'))
    store.apply(email(event_id='reply-1'))
    assert store.snapshot()['requests'][0]['status'] == 'resolved'


def test_failed_change_does_not_reserve_receipt(tmp_path):
    store = Store(tmp_path / 'test.sqlite3')
    with pytest.raises(KeyError):
        store.apply(dict(source='teacher', ref='SUP-MISSING', event_id='oops', status='resolved'))
    assert store.snapshot()['cursor'] == 0
    with store.connect() as db:
        assert db.execute('SELECT count(*) FROM receipts').fetchone()[0] == 0


def test_websocket_commit_snapshot_dedup_validation_and_restart(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_PATH', str(tmp_path / 'api.sqlite3'))
    monkeypatch.setenv('GOOGLE_TOKEN_FILE', str(tmp_path / 'no-token.json'))
    from backend import main
    main = importlib.reload(main)
    with TestClient(main.app) as client:
        with client.websocket_connect('/ws') as ws:
            initial = ws.receive_json()
            assert initial['cursor'] == 0
            assert client.post('/api/events', json=email()).json()['applied']
            arrived = ws.receive_json()
            # Poll status can also deliver an initial snapshot.
            while arrived['cursor'] == 0:
                arrived = ws.receive_json()
            assert arrived['requests'][0]['status'] == 'new'
            assert Store(main.store.path).snapshot()['cursor'] == arrived['cursor']
            assert client.post('/api/events', json=email()).json() == {'applied': False}
            assert client.post('/api/events', json=calendar()).status_code == 200
            assert ws.receive_json()['requests'][0]['status'] == 'scheduled'
            assert client.patch('/api/requests/SUP-CLASS001', json={'status': 'resolved'}).status_code == 200
            assert ws.receive_json()['requests'][0]['status'] == 'resolved'
        assert client.post('/api/events', json={**calendar(), 'version': 'bad'}).status_code == 422
        assert client.patch('/api/requests/SUP-MISSING', json={'status': 'resolved'}).status_code == 404
        assert client.post('/api/demo', headers={'Origin': 'https://untrusted.example'}).status_code == 403
        monkeypatch.setenv('GOOGLE_CLIENT_FILE', str(tmp_path / 'missing-client.json'))
        assert client.post('/api/google/connect').status_code == 503
    main = importlib.reload(main)
    with TestClient(main.app) as client:
        with client.websocket_connect('/ws') as ws:
            assert ws.receive_json()['requests'][0]['status'] == 'resolved'
        assert client.get('/api/snapshot').json()['cursor'] == 3


def test_durable_demo_queue_survives_restart(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_PATH', str(tmp_path / 'demo.sqlite3'))
    monkeypatch.setenv('GOOGLE_TOKEN_FILE', str(tmp_path / 'no-token.json'))
    from backend import main
    main = importlib.reload(main)
    with TestClient(main.app) as client:
        ref = client.post('/api/demo').json()['ref']
    with main.store.connect() as db:
        assert db.execute('SELECT count(*) FROM pending_demo').fetchone()[0] >= 2
        db.execute("UPDATE pending_demo SET due='2000-01-01T00:00:00+00:00'")
    main = importlib.reload(main)
    with TestClient(main.app) as client:
        with client.websocket_connect('/ws') as ws:
            result = ws.receive_json()
            while result['cursor'] < 3:
                result = ws.receive_json()
            assert result['requests'][0]['ref'] == ref
            assert result['requests'][0]['status'] == 'scheduled'
            assert len(result['activity']) == 3


def test_google_metadata_only_paging_and_deleted_tombstone(tmp_path, monkeypatch):
    from backend import google_sync
    store = Store(tmp_path / 'google.sqlite3')
    store.apply(email())
    store.apply({**calendar(), 'calendar_id': 'primary:lesson-1'})
    calls = []

    class Call:
        def __init__(self, result): self.result = result
        def execute(self): return self.result

    class Gmail:
        def users(self): return self
        def messages(self): return self
        def list(self, **kw):
            calls.append(('list', kw))
            return Call({'messages': [{'id': 'google-1'}], 'nextPageToken': 'page2'} if not kw['pageToken'] else {})
        def get(self, **kw):
            calls.append(('get', kw))
            return Call({'payload': {'headers': [{'name': 'Subject', 'value': '[SUP-CLASS001] Help'}]}})

    class Calendar:
        def events(self): return self
        def list(self, **kw):
            calls.append(('calendar', kw))
            # Real Google deletion tombstones guarantee only id, not summary/updated/start.
            return Call({'items': [{'id': 'lesson-1', 'status': 'cancelled'}], 'nextSyncToken': 'sync-2'})

    class Credentials:
        expired = False
        @classmethod
        def from_authorized_user_file(cls, *args): return cls()

    monkeypatch.setattr(google_sync, 'Credentials', Credentials)
    monkeypatch.setattr(google_sync, 'build', lambda service, *a, **kw: Gmail() if service == 'gmail' else Calendar())
    events, key, checkpoint = google_sync.poll(store)
    assert store.checkpoint(key) is None  # Fetching cannot advance the committed checkpoint.
    for e in events: store.apply(e)
    store.checkpoint(key, checkpoint)
    assert store.snapshot()['requests'][0]['status'] == 'needs_follow_up'
    assert store.checkpoint(key) == 'sync-2'
    assert len([c for c in calls if c[0] == 'list']) == 2
    assert next(c[1] for c in calls if c[0] == 'get')['format'] == 'metadata'
    assert next(c[1] for c in calls if c[0] == 'get')['metadataHeaders'] == ['Subject']
    assert google_sync.reference('[SUP-ONE] [SUP-TWO]') is None
