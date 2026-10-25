import sqlite3
import time
import unittest
from unittest.mock import patch

import jwt
import test_api
from auth_handlers import LoginLimit
from test_api import TRIP
from tokens import AUDIENCE, ISSUER, verify_token


class AuthTests(unittest.TestCase):
    setUp = test_api.ApiTests.setUp
    tearDown = test_api.ApiTests.tearDown
    start_server = test_api.ApiTests.start_server
    stop_server = test_api.ApiTests.stop_server
    call = test_api.ApiTests.call
    data = test_api.ApiTests.data

    def auth(self, route='login', **values):
        return self.data('POST', '/api/auth/' + route, values or {
            'email': 'class@example.com', 'password': 'class-test-password'})

    def test_login_and_hashed_credentials(self):
        status, session = self.auth()
        self.assertEqual(status, 200)
        self.assertEqual(session['token_type'], 'Bearer')
        self.assertEqual(session['expires_in'], 3600)
        self.assertEqual(verify_token(session['access_token'], self.server.jwt_key), session['user']['id'])
        with sqlite3.connect(self.path) as connection:
            row = connection.execute('SELECT salt,password_hash FROM users').fetchone()
        self.assertNotIn('class-test-password', row)
        self.assertEqual(len(row[1]), 64)
        self.assertEqual(self.auth(password='wrong-password', email='class@example.com')[0], 401)
        self.assertEqual(self.auth(password='wrong-password', email='nobody@example.com')[0], 401)
        self.assertEqual(self.auth('register')[0], 409)
        self.assertEqual(self.data(path='/api/auth/login')[0], 405)

    def test_credential_validation_and_auth_storage_failure(self):
        for body in [[], {}, {'email': 'no-at', 'password': 'long-password'},
                     {'email': 'x' * 250 + '@a.com', 'password': 'long-password'},
                     {'email': 'x@a.com', 'password': 'short'},
                     {'email': 'x@a.com', 'password': 123}]:
            self.assertEqual(self.data('POST', '/api/auth/register', body)[0], 400)
        self.server.login_limit = LoginLimit()
        with sqlite3.connect(self.path) as connection:
            connection.execute('DROP TABLE users')
        self.assertEqual(self.auth()[0], 503)

    def test_missing_tampered_expired_wrong_claims_and_deleted_user(self):
        user_id = verify_token(self.token, self.server.jwt_key)
        claims = {'sub': user_id, 'iat': int(time.time()), 'exp': int(time.time()) + 60,
                  'iss': ISSUER, 'aud': AUDIENCE}
        expired = {**claims, 'iat': int(time.time()) - 100, 'exp': int(time.time()) - 1}
        variants = ['', 'Basic value', 'Bearer invalid', 'Bearer ' + 'x' * 4097,
                    'Bearer ' + jwt.encode(claims, 'incorrect-key' * 4, algorithm='HS256'),
                    'Bearer ' + jwt.encode(expired, self.server.jwt_key, algorithm='HS256'),
                    'Bearer ' + jwt.encode({**claims, 'aud': 'wrong'}, self.server.jwt_key, algorithm='HS256'),
                    'Bearer ' + jwt.encode({**claims, 'iss': 'wrong'}, self.server.jwt_key, algorithm='HS256'),
                    'Bearer ' + jwt.encode({'sub': user_id}, self.server.jwt_key, algorithm='HS256')]
        for header in variants:
            self.assertEqual(self.data(headers={'Authorization': header})[0], 401)
        self.assertEqual(self.data(headers={'Authorization': 'bearer ' + self.token})[0], 200)
        with sqlite3.connect(self.path) as connection:
            connection.execute('DELETE FROM users')
        self.assertEqual(self.data()[0], 401)

    def test_accounts_cannot_read_update_delete_or_assign_each_others_trips(self):
        _, trip = self.data('POST', body=TRIP)
        route = f"/api/trips/{trip['id']}"
        _, second = self.auth('register', email='SECOND@EXAMPLE.COM', password='second-password')
        self.assertEqual(second['user']['email'], 'second@example.com')
        original = self.token
        self.token = second['access_token']
        self.assertEqual(self.data()[1], [])
        for method in ['GET', 'PUT', 'DELETE']:
            self.assertEqual(self.data(method, route, TRIP if method == 'PUT' else None)[0], 404)
        self.assertEqual(self.data('POST', body={**TRIP, 'owner_id': trip['owner_id']})[0], 400)
        self.assertEqual(self.data('POST', body=TRIP)[0], 201)
        self.token = original
        self.assertEqual(self.data()[1], [trip])

    def test_auth_rate_limit_and_window_reset(self):
        self.server.login_limit = LoginLimit()
        for _ in range(10):
            self.assertEqual(self.auth()[0], 200)
        self.assertEqual(self.auth()[0], 429)
        limiter = LoginLimit()
        with patch('auth_handlers.time.monotonic', return_value=1):
            self.assertTrue(limiter.allow('local'))
        with patch('auth_handlers.time.monotonic', return_value=62):
            self.assertTrue(limiter.allow('local'))
        self.assertEqual(len(limiter.attempts['local']), 1)
