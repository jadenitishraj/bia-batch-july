"""Public account endpoints and Bearer-token authorization for trip routes."""
import time
from collections import defaultdict, deque
from threading import Lock

import accounts
import jwt
from tokens import TOKEN_SECONDS, issue_token, verify_token


class LoginLimit:
    def __init__(self):
        self.attempts = defaultdict(deque)
        self.lock = Lock()

    def allow(self, address):
        with self.lock:
            attempts = self.attempts[address]
            now = time.monotonic()
            while attempts and attempts[0] <= now - 60:
                attempts.popleft()
            if len(attempts) >= 10:
                return False
            attempts.append(now)
            return True


class AuthHandlers:
    def auth_route(self, path):
        if path not in {'/api/auth/register', '/api/auth/login'}:
            return False
        if self.command != 'POST':
            self.respond(405, {'error': 'Method not allowed.'})
            return True
        if not self.server.login_limit.allow(self.client_address[0]):
            self.respond(429, {'error': 'Too many attempts. Please wait one minute.'})
            return True
        email, password = accounts.validate_credentials(self.read_json())
        create = path.endswith('/register')
        user = (accounts.register if create else accounts.authenticate)(
            self.database_path, email, password)
        if user is None:
            self.respond(409 if create else 401, {'error': 'Account already exists.' if create
                         else 'Invalid email or password.'})
            return True
        self.respond(201 if create else 200, {'access_token': issue_token(user['id'], self.server.jwt_key),
                     'token_type': 'Bearer', 'expires_in': TOKEN_SECONDS, 'user': user})
        return True

    def authorize(self):
        scheme, _, token = self.headers.get('Authorization', '').partition(' ')
        try:
            if scheme.lower() != 'bearer' or not token or len(token) > 4096:
                raise jwt.InvalidTokenError()
            user_id = verify_token(token, self.server.jwt_key)
            self.user = accounts.find_user(self.database_path, user_id)
            if self.user is None:
                raise jwt.InvalidTokenError()
        except jwt.InvalidTokenError:
            self.respond(401, {'error': 'Please log in again. Your token is missing or invalid.'})
            return False
        return True
