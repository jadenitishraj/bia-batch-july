"""Run the real graph and SDK against the local Postman Bedrock stand-in."""
import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend' / 'tests'))


def main():
    from chat_support import ChatServer
    # Fake credentials sign local requests only. No real AWS call is made.
    os.environ.update(AWS_ACCESS_KEY_ID='simulation', AWS_SECRET_ACCESS_KEY='simulation',
                      AWS_ENDPOINT_URL_BEDROCK_RUNTIME='http://127.0.0.1:4519/bedrock')
    os.environ.pop('AWS_SESSION_TOKEN', None)
    with ChatServer() as api:
        for action in ['create-test', 'update-test', 'delete-test', 'throttle-test']:
            response = httpx.post(api.base + '/api/chat', json={'message': action},
                                  headers={'Authorization': api.token}, timeout=20)
            trips = api.call('/api/trips')[1]
            if action == 'create-test':
                assert response.status_code == 200 and len(trips) == 1
                original_plan = trips[0]['plan']
            elif action == 'update-test':
                assert response.status_code == 200 and trips[0]['budget'] == 25000
                assert trips[0]['plan'] == original_plan
            elif action == 'delete-test':
                assert response.status_code == 200 and trips == []
            else:
                assert response.status_code == 503 and trips == []
                assert 'Bedrock could not finish' in response.json()['error']
            print(action + ' passed')


if __name__ == '__main__':
    main()
