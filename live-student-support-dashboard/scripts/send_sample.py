"""No Google credentials: replay the same payloads to demonstrate deduplication."""
import json
import urllib.request

BASE = 'http://127.0.0.1:8000'
events = [
    dict(source='gmail', event_id='sample-email-001', ref='SUP-CLASS001',
         title='[SUP-CLASS001] Help understanding FastAPI background tasks'),
    dict(source='calendar', event_id='sample-calendar-001-v1', ref='SUP-CLASS001',
         calendar_id='sample-tutoring-001', version='2026-11-22T10:00:00Z',
         start='2026-11-23T14:30:00+05:30', cancelled=False),
]
for event in events:
    req = urllib.request.Request(BASE + '/api/events', data=json.dumps(event).encode(),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as response:
        print(event['source'], response.read().decode())
print('Run again: both applied values should be false. Watch the dashboard in a second window.')
