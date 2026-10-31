"""Shared HTTP input/output rules, separate from application routing."""
import json

from validation import validate_trip

MAX_BODY = 100000


class HttpHelpers:
    def respond(self, status, value):
        payload = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        if status == 401:
            self.send_header('WWW-Authenticate', 'Bearer')
        if status == 429:
            self.send_header('Retry-After', '60')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(payload)

    def allow_write(self):
        origin = self.headers.get('Origin')
        expected = 'http://' + self.headers.get('Host', '')
        allowed_origins = {expected, 'http://127.0.0.1:5175', 'http://localhost:5175'}
        if origin and origin not in allowed_origins:
            self.respond(403, {'error': 'Cross-origin changes are not allowed.'})
            return False
        return True

    def read_payload(self):
        return validate_trip(self.read_json())

    def read_json(self):
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            raise ValueError('Send application/json.')
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            raise ValueError('Invalid request length.') from None
        if not 0 < length <= MAX_BODY:
            raise ValueError('Request must contain JSON smaller than 100 KB.')
        try:
            return json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ValueError('Invalid JSON.') from None
