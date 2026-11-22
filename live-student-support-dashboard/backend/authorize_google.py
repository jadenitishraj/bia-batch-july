"""Run manually, with the backend stopped: python -m backend.authorize_google."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from backend.google_sync import SCOPES, save_token


def main():
    load_dotenv()
    client = Path(os.getenv('GOOGLE_CLIENT_FILE', '.local/google-client.json'))
    if not client.is_file():
        raise SystemExit('Missing Desktop OAuth client JSON. See README: Connect real Google data.')
    automate = '--automation' in sys.argv
    if automate:
        from backend.automation import SCOPES as requested, token_path
    else:
        requested = SCOPES
    flow = InstalledAppFlow.from_client_secrets_file(str(client), requested, autogenerate_code_verifier=True)
    credentials = flow.run_local_server(host='127.0.0.1', port=0, open_browser=True, timeout_seconds=300, prompt='consent',
                                        authorization_prompt_message='Opening Google consent in your browser…',
                                        success_message='Connected. You can close this tab and start the dashboard backend.')
    if not credentials.has_scopes(requested):
        raise SystemExit('Required scopes were not granted; existing authorization was preserved.')
    save_token(credentials, token_path() if automate else None)
    print('Authorization saved privately. Proposal monitoring remains off until enabled; every booking requires approval.' if automate else 'Read-only authorization saved locally.')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        raise SystemExit('Authorization did not complete. Check Google consent/client setup and try again.')
