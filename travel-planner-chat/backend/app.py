"""Local-only Python web server. Run: python3 app.py."""
import argparse
import json
import re
import sqlite3
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import database
from trip_handlers import TripHandlers
from validation import validate_trip

MAX_BODY = 100000


class Handler(TripHandlers, BaseHTTPRequestHandler):
    def __init__(self, *args, database_path, **kwargs):
        self.database_path = database_path
        super().__init__(*args, **kwargs)

    def respond(self, status, value):
        payload = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        self.dispatch(self.get_trips)

    def do_POST(self):
        self.dispatch(self.create_trip, scope='collection')

    def do_PUT(self):
        self.dispatch(self.update_trip, scope='item')

    def do_DELETE(self):
        self.dispatch(self.delete_trip, scope='item')

    def allow_write(self):
        origin = self.headers.get('Origin')
        expected = 'http://' + self.headers.get('Host', '')
        allowed_origins = {expected, 'http://127.0.0.1:5175', 'http://localhost:5175'}
        if origin and origin not in allowed_origins:
            self.respond(403, {'error': 'Cross-origin changes are not allowed.'})
            return False
        return True

    def read_payload(self):
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            raise ValueError('Send application/json.')
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            raise ValueError('Invalid request length.') from None
        if not 0 < length <= MAX_BODY:
            raise ValueError('Request must contain JSON smaller than 100 KB.')
        try:
            return validate_trip(json.loads(self.rfile.read(length)))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ValueError('Invalid JSON.') from None

    def dispatch(self, action, *, scope='any'):
        if self.command != 'GET' and not self.allow_write():
            return
        path = urlsplit(self.path).path
        match = re.fullmatch(r'/api/trips/([1-9][0-9]{0,17})', path)
        trip_id = int(match[1]) if match else None
        collection = path == '/api/trips'
        if not collection and not match:
            self.respond(404, {'error': 'Not found.'})
            return
        if (scope == 'item' and collection) or (scope == 'collection' and match):
            self.respond(405, {'error': 'Method not allowed.'})
            return
        try:
            action(trip_id)
        except ValueError as error:
            self.respond(400, {'error': str(error)})
        except sqlite3.Error:
            self.respond(503, {'error': 'Database unavailable. Please try again.'})


def create_server(port=8003, database_path=database.DEFAULT_DATABASE):
    database.initialize(database_path)
    return ThreadingHTTPServer(('127.0.0.1', port), partial(Handler, database_path=database_path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8003)
    parser.add_argument('--database', type=Path, default=database.DEFAULT_DATABASE)
    options = parser.parse_args()
    server = create_server(options.port, options.database)
    print(f'Travel Planner Chat: http://127.0.0.1:{server.server_port}/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
