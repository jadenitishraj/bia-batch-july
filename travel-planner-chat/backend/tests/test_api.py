import json
import sqlite3
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_server

TRIP = dict(title='Singapore escape', destination='Singapore', days=4,
            travelers=2, budget=85000, plan='Day 1 — Arrive\nRelax.\n\nDay 2 — Explore\nGardens.')


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = Path(self.folder.name) / 'data' / 'trips.db'
        self.start_server()

    def start_server(self):
        self.server = create_server(0, self.path)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_port}'

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def tearDown(self):
        self.stop_server()
        self.folder.cleanup()

    def call(self, method='GET', path='/api/trips', body=None, raw=None, headers=None):
        content = json.dumps(body).encode() if body is not None else raw
        request = Request(self.base + path, data=content, method=method,
                          headers=headers or {'Content-Type': 'application/json'})
        try:
            response = urlopen(request)
        except HTTPError as error:
            response = error
        with response:
            return response.status, response.read(), response.headers

    def data(self, *args, **kwargs):
        status, payload, _ = self.call(*args, **kwargs)
        return status, json.loads(payload)

    def test_full_crud_and_persistence_after_server_restart(self):
        self.assertEqual(self.data(), (200, []))
        status, created = self.data('POST', body=TRIP)
        self.assertEqual(status, 201)
        self.assertEqual(created['plan'], TRIP['plan'])
        route = f"/api/trips/{created['id']}"
        self.assertEqual(self.data(path=route), (200, created))
        self.stop_server()
        self.start_server()
        self.assertEqual(self.data()[1], [created])
        updated = {**TRIP, 'title': 'New title', 'plan': 'Day 1\nA new plan.'}
        status, saved = self.data('PUT', route, updated)
        self.assertEqual(status, 200)
        self.assertEqual(saved['title'], 'New title')
        self.assertEqual(saved['plan'], updated['plan'])
        self.assertEqual(self.data('DELETE', route), (200, {'deleted': True}))
        self.assertEqual(self.data()[1], [])
        for method in ['GET', 'PUT', 'DELETE']:
            self.assertEqual(self.data(method, route, updated if method == 'PUT' else None)[0], 404)

    def test_input_validation_preserves_database(self):
        invalid = [[], {}, {**TRIP, 'extra': 'field'}, {**TRIP, 'title': ' '},
                   {**TRIP, 'title': 'a' * 101}, {**TRIP, 'destination': None},
                   {**TRIP, 'plan': 'a' * 20001}, {**TRIP, 'days': 0},
                   {**TRIP, 'days': True}, {**TRIP, 'days': 1.5},
                   {**TRIP, 'travelers': 101}, {**TRIP, 'budget': -1}]
        for value in invalid:
            with self.subTest(value=str(value)[:80]):
                self.assertEqual(self.data('POST', body=value)[0], 400)
        for raw in [b'no json', b'\xff', b'']:
            self.assertEqual(self.data('POST', raw=raw)[0], 400)
        self.assertEqual(self.data('POST', body=TRIP, headers={'Content-Type': 'text/plain'})[0], 400)
        self.assertEqual(self.data('POST', raw=b'x' * 100001)[0], 400)
        self.assertEqual(self.data()[1], [])

    def test_trims_strings_and_stores_sql_and_html_as_plain_text(self):
        value = {**TRIP, 'title': "  Robert'); DROP TABLE trips;--  ",
                 'plan': '<img src=x onerror=alert(1)>'}
        status, trip = self.data('POST', body=value)
        self.assertEqual(status, 201)
        self.assertEqual(trip['title'], value['title'].strip())
        self.assertEqual(self.data()[1][0]['plan'], value['plan'])
        self.assertEqual(self.data('POST', body=TRIP)[0], 201)

    def test_routing_and_cross_origin_mutations(self):
        for path in ['/missing', '/api/trips/0', '/api/trips/abc', '/api/trips/1/extra']:
            self.assertEqual(self.data(path=path)[0], 404)
        self.assertEqual(self.data('PUT', body=TRIP)[0], 405)
        self.assertEqual(self.data('DELETE')[0], 405)
        self.assertEqual(self.data('POST', '/api/trips/1', TRIP)[0], 405)
        self.assertEqual(self.data('POST', body=TRIP, headers={
            'Content-Type': 'application/json', 'Origin': 'https://unrelated.example'})[0], 403)
        self.assertEqual(self.data('POST', body=TRIP, headers={
            'Content-Type': 'application/json', 'Origin': self.base})[0], 201)

    def test_vite_development_origin_can_save(self):
        self.assertEqual(self.data('POST', body=TRIP, headers={
            'Content-Type': 'application/json', 'Origin': 'http://127.0.0.1:5175'})[0], 201)

    def test_database_unavailable(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute('DROP TABLE trips')
        status, payload = self.data()
        self.assertEqual(status, 503)
        self.assertEqual(payload['error'], 'Database unavailable. Please try again.')


if __name__ == '__main__':
    unittest.main()
