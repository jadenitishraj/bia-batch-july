"""Local-only Python web server. Run: python3 app.py."""
import argparse
import re
import sqlite3
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import database
from auth_handlers import AuthHandlers, LoginLimit
from chat_handlers import ChatHandlers
from http_helpers import HttpHelpers
from tokens import signing_key
from trip_handlers import TripHandlers


class Handler(AuthHandlers, TripHandlers, ChatHandlers, HttpHelpers, BaseHTTPRequestHandler):
    def __init__(self, *args, database_path, **kwargs):
        self.database_path = database_path
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self.dispatch(self.get_trips)

    def do_POST(self):
        self.dispatch(self.create_trip, scope='collection')

    def do_PUT(self):
        self.dispatch(self.update_trip, scope='item')

    def do_DELETE(self):
        self.dispatch(self.delete_trip, scope='item')

    def dispatch(self, action, *, scope='any'):
        if self.command != 'GET' and not self.allow_write():
            return
        try:
            self.route(action, scope)
        except ValueError as error:
            self.respond(400, {'error': str(error)})
        except sqlite3.Error:
            self.respond(503, {'error': 'Database unavailable. Please try again.'})

    def route(self, action, scope):
        path = urlsplit(self.path).path
        if self.auth_route(path) or self.chat_route(path):
            return
        match = re.fullmatch(r'/api/trips/([1-9][0-9]{0,17})', path)
        trip_id = int(match[1]) if match else None
        collection = path == '/api/trips'
        if not collection and not match:
            self.respond(404, {'error': 'Not found.'})
            return
        if (scope == 'item' and collection) or (scope == 'collection' and match):
            self.respond(405, {'error': 'Method not allowed.'})
            return
        if self.authorize():
            action(trip_id)


def create_server(port=8003, database_path=database.DEFAULT_DATABASE):
    database.initialize(database_path)
    key = signing_key(database_path)
    server = ThreadingHTTPServer(('127.0.0.1', port), partial(Handler, database_path=database_path))
    server.jwt_key = key
    server.login_limit = LoginLimit()
    server.chat_limit = LoginLimit()
    return server


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
