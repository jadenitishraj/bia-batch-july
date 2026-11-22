# Student Support Easy — email to meeting, explained simply

This is a **new teaching project**, alongside the original `live-student-support-dashboard`. The original project is preserved.

One simple flow:

```text
New incoming email with BIA in its subject
  → save it in SQLite
  → find the next free 30 minutes, 9 am–5 pm India time
  → create a Calendar meeting and invite the sender
  → send a threaded confirmation
  → update the React chat and request table through WebSocket
```

No labels, support-reference codes, proposals, or approvals are required in **Easy**. `BIA` is matched case-insensitively in the subject. Each qualifying incoming message is one request. Only messages received after Easy's first start are eligible; old mail is not backfilled.

## Read the files in this order

| File | What it teaches |
| --- | --- |
| `backend/main.py` | Start the application and background task |
| `backend/routes.py` | The HTTP and WebSocket endpoints React calls |
| `backend/background.py` | A short loop that checks Gmail |
| `backend/live.py` | Push saved data to open browsers |
| `backend/workflow.py` | The email-to-meeting steps, written in order |
| `backend/database.py` | SQLite saves request progress and notifications |
| `backend/gmail.py` | Read headers and send a reply in the same thread |
| `backend/calendar.py` | Check busy times and create one meeting |
| `backend/google_login.py` | Reuse Google's already-approved consent |
| `backend/ai.py` | Stream real Gemini response chunks over HTTP |
| `backend/settings.py` | The few values we can change |
| `frontend/src/App.jsx` | React chat and the adjacent saved-request table |

Use plain functions and small comments. There is intentionally no agent framework, approval system, generic workflow engine, report builder, or production retry system here.

## Run

From the repository root, enter `student-support-easy`. Python 3.12 and Node 20.19+ or 22.12+ are recommended. Complete the Google setup below before running the real Gmail flow.

```bash
cd student-support-easy
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -r requirements.lock.txt
cp -n .env.example .env
# Set your own GEMINI_API_KEY in .env before starting chat.
uvicorn backend.main:app --host 127.0.0.1 --port 8002
```

In another terminal:

```bash
cd student-support-easy/frontend
npm ci
npm run dev
```

Open the Vite URL printed in the terminal. For one-process serving, run `npm run build` in `frontend`, restart FastAPI, and open `http://127.0.0.1:8002`.

## Google and Gemini setup

Gemini uses your own key from this app's ignored `.env`: set `GEMINI_API_KEY` and, if needed, `GEMINI_MODEL`. `GOOGLE_API_KEY` is also accepted. The default model is `gemini-3.5-flash-lite`; model access depends on your account. An optional explicit `GEMINI_ENV_FILE` can supply just those Gemini fields from another authorized file. Nothing searches other projects for keys automatically. Credentials never go to React or Gemini's prompt.

Google OAuth is separate. Signing into Gmail in your browser does not authorize this Python app. No Google credentials or consent are shipped in this repository.

For a fresh machine, use the sibling [Classroom AI setup guide](../live-student-support-dashboard/README.md#real-google-connection-read-only) to create your own Google Cloud project, enable Gmail/Calendar APIs, configure Desktop OAuth consent and a test user, and save your client JSON privately. Install that app's locked Python dependencies, then run `python -m backend.authorize_google --automation` from its own folder and personally approve the requested permissions. This saves its private automation token; you do not need to enable its proposal monitoring or run its server.

Easy defaults to that sibling token path. Alternatively, set `EASY_GOOGLE_TOKEN` to an already-consented authorized-user token file you own. Required scopes are Gmail read/send, Calendar event writes on owned calendars, and free/busy availability. The original setup also requests Calendar event read. Refresh uses Google's normal credentials library. If consent expires, repeat the original authorization command. Never commit client JSON or token files.

Easy starts its automatic watcher when its server starts. There is no approval step: a **new incoming email with BIA in its subject** can create a meeting, invite its sender, and send confirmation. Use a classroom account and synthetic requests for lessons.

The default calendar is `primary`. Availability checks cover that calendar. Times are India time, 09:00–17:00, every day; no weekday restriction. Only the actual From sender is invited. The message body is never read or sent to Gemini. Automatic replies and Calendar notification messages are ignored so the app does not reply to its own replies.

## Four main concepts

1. **Gmail trigger:** Python checks for new incoming mail every 15 seconds. This is polling, not a Gmail webhook.
2. **SQLite state:** Each message ID is saved once. The saved status shows where the workflow stopped. Requests and notifications survive restart.
3. **WebSocket:** The server pushes a fresh saved snapshot to React after a workflow change. React redraws the chat notifications and table without refreshing. Reconnect loads the snapshot again.
4. **Streaming:** Gemini text arrives in pieces through a separate HTTP stream. React adds each piece to that particular assistant bubble. A live email notification can arrive at the same time.

Ask “What requests have I received so far?” or “Which meetings have been scheduled?” The chatbot reads saved SQLite request fields for those answers. General questions still use Gemini normally. The table always shows **all saved requests** and their current statuses. Ordinary AI chat turns live in browser memory; saved workflow notices and the table return after reload.

## Safe classroom check

Use **Add a sample request** to see SQLite, WebSocket updates and the table without sending email or creating an actual meeting. Samples are labeled Demo.

For the real flow, after Easy is running send a **new** email whose subject includes `BIA`. The next poll should show the email, meeting time, and confirmation status. Easy is explicitly automatic: there is no approval screen. Do not use private student data for the lesson. No real test message or invitation is sent merely by installing this project.

Each Gmail message ID is saved once in SQLite. The workflow skips any email already recorded, including after restart. This keeps the lesson simple and prevents automatic retries from repeating a meeting or email. If a step fails, the request says **needs review**. If the server stops partway through, its last status remains visible; inspect Calendar and Sent manually. There is no automatic recovery or retry system. Calendar still uses one event ID per email. Availability checking and event creation are separate calls, so another Calendar client can race the check.

The first-start cutoff is kept in SQLite. Do not delete the database to retry a real email or uncertain send; inspect Calendar/Sent first. Deleting the database starts a new cutoff and clears this project's local history. Run one local server process; this app has no public-user authentication and should remain bound to localhost.
