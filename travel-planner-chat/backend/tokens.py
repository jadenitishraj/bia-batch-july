"""JWT signing and verification with a server-only persistent local key."""
import os
import secrets
import time
from pathlib import Path

import jwt
from dotenv import load_dotenv

ISSUER = 'travel-planner-chat'
AUDIENCE = 'travel-planner-api'
TOKEN_SECONDS = 3600


def signing_key(database_path):
    load_dotenv(Path(__file__).with_name('.env'), override=False)
    configured = os.environ.get('JWT_SECRET')
    if configured is not None:
        if len(configured.encode()) < 32:
            raise ValueError('JWT_SECRET must contain at least 32 bytes.')
        return configured
    path = Path(database_path).with_suffix('.jwt-key')
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        key = path.read_text()
    else:
        key = secrets.token_hex(32)
        with os.fdopen(descriptor, 'w') as output:
            output.write(key)
    if len(key.encode()) < 32:
        raise ValueError('Local JWT signing key is invalid.')
    return key


def issue_token(user_id, key):
    now = int(time.time())
    claims = {'sub': user_id, 'iat': now, 'exp': now + TOKEN_SECONDS,
              'iss': ISSUER, 'aud': AUDIENCE}
    return jwt.encode(claims, key, algorithm='HS256')


def verify_token(token, key):
    claims = jwt.decode(token, key, algorithms=['HS256'], issuer=ISSUER, audience=AUDIENCE,
                        options={'require': ['sub', 'iat', 'exp', 'iss', 'aud']})
    return claims['sub']
