"""Local accounts: salted password hashes, never plaintext passwords."""
import hashlib
import hmac
import re
import secrets
import sqlite3
import uuid
from contextlib import closing

from database import connect

ITERATIONS = 600000


def validate_credentials(values):
    if not isinstance(values, dict) or set(values) != {'email', 'password'}:
        raise ValueError('Send email and password only.')
    email, password = values['email'], values['password']
    if not isinstance(email, str) or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email.strip()):
        raise ValueError('Enter a valid email address.')
    if len(email) > 254:
        raise ValueError('Email is too long.')
    if not isinstance(password, str) or not 8 <= len(password) <= 128:
        raise ValueError('Password must contain 8 to 128 characters.')
    return email.strip().lower(), password


def password_hash(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), ITERATIONS).hex()


def register(path, email, password):
    salt = secrets.token_hex(16)
    user_id = str(uuid.uuid4())
    digest = password_hash(password, salt)
    try:
        with closing(connect(path)) as connection, connection:
            connection.execute('INSERT INTO users VALUES (?,?,?,?)', (user_id, email, salt, digest))
    except sqlite3.IntegrityError:
        return None
    return {'id': user_id, 'email': email}


def authenticate(path, email, password):
    with closing(connect(path)) as connection:
        row = connection.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
    salt = row['salt'] if row else '00' * 16
    expected = row['password_hash'] if row else '00' * 32
    matches = hmac.compare_digest(password_hash(password, salt), expected)
    return {'id': row['id'], 'email': row['email']} if row and matches else None


def find_user(path, user_id):
    with closing(connect(path)) as connection:
        row = connection.execute('SELECT id,email FROM users WHERE id=?', (user_id,)).fetchone()
    return dict(row) if row else None
