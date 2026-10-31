"""Disposable real HTTP server used by chat and tool tests."""
import json
import sys
import tempfile
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_server

TRIP = dict(title='Jaipur weekend', destination='Jaipur', days=3,
            travelers=2, budget=20000, plan='Day 1 — Explore the old city.')


class ChatServer:
    def __enter__(self):
        self.folder = tempfile.TemporaryDirectory()
        self.server = create_server(0, Path(self.folder.name) / 'trips.db')
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_port}'
        self.token = self.register('one@example.test')
        return self

    def __exit__(self, *_args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.folder.cleanup()

    def register(self, email):
        _, data = self.call('/api/auth/register', 'POST', {
            'email': email, 'password': 'Classroom-test-password'})
        return 'Bearer ' + data['access_token']

    def call(self, path, method='GET', body=None, token=None):
        request = Request(self.base + path, method=method,
                          data=json.dumps(body).encode() if body is not None else None,
                          headers={'Content-Type': 'application/json',
                                   'Authorization': token or getattr(self, 'token', '')})
        try:
            response = urlopen(request, timeout=10)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)
