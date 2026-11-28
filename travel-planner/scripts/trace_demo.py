"""Run the live app's fixed synthetic trace demo without exposing credentials."""
import json
import os

import httpx


def main():
    base = os.getenv('TRAVEL_PLANNER_URL', 'http://127.0.0.1:5174')
    completed = False
    with httpx.stream('POST', base + '/api/observability/demo', timeout=120) as response:
        if response.status_code != 200:
            raise SystemExit(f'Demo unavailable: HTTP {response.status_code}. Check private tracing settings.')
        for line in response.iter_lines():
            if not line:
                continue
            event = json.loads(line)
            if event['type'] == 'step':
                print('Completed step:', event['node'], flush=True)
            elif event['type'] == 'error':
                print(event['message'], flush=True)
            elif event['type'] == 'done':
                completed = True
            elif event['type'] == 'trace':
                print('Trace ID:', event['run_id'])
                print('LangSmith project:', event['project'])
    print('Workflow completed:', completed)
    print('Confirm ingestion in LangSmith; a trace ID alone does not prove export succeeded.')
    return 0 if completed else 1


if __name__ == '__main__':
    raise SystemExit(main())
