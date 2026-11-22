# Live Student Support Dashboard — Classroom AI

An AI teaching app in the existing BIA July repository. The main interface is **one conversation**: ask Gemini general questions or questions about locally tracked support requests. Gmail support emails and Calendar tutoring changes proactively appear as messages, even while an AI reply is streaming. There are no request lists or statistics cards.

This builds on the repository's **FastAPI, Webhooks & Background Tasks** deck and **GitHub Issue Agent**. Python/FastAPI, React/Vite, SQLite, and WebSockets remain. Read-only operation is the default. Optional proposal monitoring can check availability; a meeting, actual-sender invitation and threaded confirmation require your approval of a specific proposal after separate Google consent.

## Run the chat

Python 3.11+ and Node 20.19+ / 22.12+ are required. This machine's default `python3` is 3.9; use `uv` to select 3.12.

Terminal 1:

```bash
cd live-student-support-dashboard
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -r backend/requirements.lock.txt
# Only for a fresh setup; do not overwrite an existing .env or credentials.
cp -n .env.example .env
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```bash
cd live-student-support-dashboard/frontend
npm ci
npm run dev
```

Open [Classroom AI](http://127.0.0.1:5173). API docs are at [port 8000/docs](http://127.0.0.1:8000/docs).

For a single process: run `npm run build` in `frontend` **before starting/restarting FastAPI**, then open [port 8000](http://127.0.0.1:8000). Vite proxies `/api` and `/ws` during development; the production build is served directly by FastAPI.

Without uv, use `python3.12 -m venv .venv` and `.venv/bin/python -m pip install -r backend/requirements.lock.txt`.

## Gemini: real incremental replies

The server uses Google's official **google-genai** Python SDK with `client.aio.models.generate_content_stream`. It does not simulate a completed answer with a typing animation. Provider text chunks are committed and emitted as they arrive.

For a fresh setup, add a Gemini API key to this app's ignored `.env`:

```dotenv
GEMINI_API_KEY=your-private-gemini-key
GEMINI_MODEL=gemini-3.5-flash-lite
APP_TIMEZONE=Asia/Kolkata
```

Restart FastAPI after configuration changes. Never prefix a secret with `VITE_`; the browser receives no API key or OAuth token. `GOOGLE_API_KEY` is also supported as a server-side alternative. Model availability depends on the key/project, so change `GEMINI_MODEL` if your account cannot access that model.

Optionally set `GEMINI_ENV_FILE` in the ignored local `.env` to reuse the Gemini key/model from another explicitly authorized local environment file. Only those fields are read; the source file is not edited and other credentials are not loaded. There is no automatic search for credentials. A direct app/environment `GEMINI_API_KEY` or `GOOGLE_API_KEY` takes precedence.

Gmail/Calendar OAuth is separate from Gemini authorization. Those OAuth credentials are never passed to Gemini. Check **Connection settings** for model presence and Google poll freshness. Presence is not presented as proof of working Gemini access; actual failures appear in the conversation.

Examples:

- “Explain WebSockets in simple terms” — general Gemini answer with no classroom records supplied.
- “Who is still waiting for a session?” — server queries saved requests in `new`, `in_progress`, or `needs_follow_up` status; Gemini explains the result.
- “When is the FastAPI tutoring session?” — server searches locally tracked FastAPI requests and provides their statuses and times to Gemini.
- “When is SUP-CLASS001?” — exact-reference lookup, with no invented learner identity.

A missing Gemini key produces an explicit 503 setup message. Quota/rate limit (429), access denial (401/403), and unavailable model (404) have specific sanitized errors. There is **no fake AI fallback**. Demo events and Google polling continue independently when Gemini is unavailable.

Official references: [Google Gen AI Python SDK](https://googleapis.github.io/python-genai/), [official SDK source](https://github.com/googleapis/python-genai), [Gemini API setup](https://ai.google.dev/gemini-api/docs/quickstart).

## Grounding, freshness, and privacy

`backend/chat.py` conservatively recognizes classroom questions from support references and words such as tutoring, session, waiting, scheduled, Gmail, Calendar, student, or tracked requests. Natural follow-ups such as “what is the status of this?”, “when is it?” and “was that scheduled?” resolve from saved references in nearby visible notifications or the most recent explicit classroom discussion. The browser sends at most ten visible message IDs, not their text. The server resolves those IDs against its own saved messages; API clients omitting IDs use recent saved conversation. A single reference triggers a fresh SQLite lookup. Multiple references in a co-arriving notification group (within ten seconds) or a discussed list require clarification. An explicitly named reference in the current question always wins. Notification subjects are never parsed as instructions or extra candidate references. This is a transparent teaching router, not an unrestricted database agent. For ambiguous questions, name the support reference or lesson topic. Generic technical questions containing words such as “session” can route to the classroom path; rephrase as a general concept question if needed.

The server executes parameterized, **read-only SELECT queries** against SQLite. Gemini cannot choose SQL, change statuses, execute code, send emails, or modify Calendar. Exact references and waiting status filters take precedence; topic words select matching titles. At most **20 relevant records**, a matching total, the query criteria, source checkpoint, capture time and last successful Google poll are supplied. Answers must disclose a partial result if the match count exceeds 20. Missing matches mean “no matching tracked records,” not “nothing exists in Gmail.”

Classroom answers identify students by support reference. For an approved live booking only, the private job ledger retains the original sender address and threading headers needed for the authorized invitation/confirmation; those fields never enter Gemini or broad notifications. General questions receive no classroom records or classroom chat history. Waiting lists omit email subjects; topic searches include only relevant truncated titles. No message bodies, snippets, attachments, Calendar descriptions or attendees, raw Google payloads, or credentials are sent to Gemini. Classroom answers receive only the current resolved query and its filtered records. A follow-up supplies only its resolved reference(s), ambiguity flag and source message ID; unrelated prior questions, assistant answers and event history are excluded. General chat uses up to six recent relevant non-classroom turns.

All supplied session times are formatted by Python in `APP_TIMEZONE` with explicit offsets; Gemini does not need to calculate time zones. The server supplies whether a stored session is active/past. A resolved request may still have a recorded session timestamp; it is not automatically a current appointment. Synthetic demo/sample records are explicitly labeled in both model context and notifications. Email/Calendar titles are **untrusted evidence**, delimited in authoritative JSON and never treated as instructions. The model has no workflow mutation tools even if an email contains instructions. AI can still make factual mistakes; check exact references and saved source records when necessary.

Questions are answered from the **last saved snapshot**, not an on-demand Google refresh. A long reply can become stale if a Calendar update arrives during generation. Its grounding checkpoint remains fixed and its reply says it is a snapshot; the new event appears separately. Ask again to use the newly saved state. Google connection errors and last-successful-poll time are included in context. Polling can lag by the configured interval plus network time.

## Classroom demo without Google or Gemini credentials

Click the compact **Run demo** button. A unique synthetic email becomes a request, then a tutoring booking arrives, then its time changes, two seconds apart. All three updates appear directly in the chat without a question or page refresh. Notifications are deterministic workflow messages, **not AI-generated text**. They remain useful if Gemini has no key or has exhausted quota.

For the fixed replay exercise, from the app root:

```bash
.venv/bin/python scripts/send_sample.py
.venv/bin/python scripts/send_sample.py
```

The second run returns `applied: false` for both events and creates no duplicate chat notifications. The fixed sample has November 2026 dates; the demo button uses dates relative to today. Creating/processing a demo makes no Google writes.

The app's classroom API remains available at `/api/events` (local normalized simulator), `/api/requests/{ref}` (local teacher status only), and `/api/snapshot`. These are not public Google webhook receivers. Teacher status can be demonstrated through `/docs`; no separate dashboard UI is required.

## Deterministic Gmail / Calendar matching

Use one immutable reference in square brackets, e.g. **`[SUP-CLASS001]`**:

- A Gmail subject must contain exactly one unique reference and match the dedicated classroom label. Its first email creates `new`; additional emails with that reference do not reset status.
- A one-off Calendar event title contains the **same exact reference**. Booking/moving it sets `scheduled`; cancellation/deletion sets `needs_follow_up`. Do not change the reference on an existing Calendar event. Cancel and create a new event if the request changes. Recurring events are excluded in this introductory lab.
- Grammar: `SUP-` plus 3–48 uppercase letters, digits, or hyphens. Two different references in one title are ignored. No fuzzy title/sender matching.
- Calendar-before-email changes are saved and reconciled when the email arrives. Known deleted events can be matched by saved event ID if Google omits the title. Deletion of an event never previously seen cannot be matched without a reference.
- UTC event versions prevent older changes from regressing a request. If multiple events share a reference, the most recently updated event wins (ID breaks ties). Keep one active tutoring event per reference in class.
- Local teacher statuses are `new`, `in_progress`, `scheduled`, `needs_follow_up`, `resolved`. A subsequent new Calendar change takes precedence. The AI cannot set them. Setting status does not erase a recorded session date; cancellation does.

## Real Google connection (read-only)

Each installation needs its own Google Cloud project, Desktop OAuth client, test user, and personal browser consent. Client configuration and refresh authorization belong in ignored files under `.local`, never in source control. Use **Connection settings → Reconnect Google** if authorization expires.

For a fresh machine/account:

1. In your [Google Cloud project](https://console.cloud.google.com/), enable Gmail API and Google Calendar API. Use a dedicated teaching project; no billing setup is needed for this lab.
2. Configure External / Testing OAuth consent, add your account as test user, and create a **Desktop app** OAuth client. Your organization may require approval. Do not use a service account for personal Gmail.
3. Download Desktop client JSON to this app's ignored `.local/google-client.json`. Never paste it into chat or commit it. The app requires `installed` JSON, not a web client.
4. Manually create Gmail label **BIA-Support** and label only synthetic classroom messages containing the reference. `GMAIL_QUERY` defaults to `label:BIA-Support` and must start with `label:`. A label is an app filter, not a permission boundary.
5. Prefer a dedicated classroom calendar; set its ID in `.env` as `GOOGLE_CALENDAR_ID` (default `primary`). Manually prepare a nonrecurring event with the same reference. Read-only mode never creates events. The optional approval-first workflow below can create a meeting only after specific approval.
6. Click **Connect Google** in Connection settings, or stop FastAPI and run `.venv/bin/python -m backend.authorize_google` from the app root. Google's official browser consent and Desktop loopback callback are used with a five-minute timeout. Personally choose the test account and approve access. Restart FastAPI after the command-line method.
7. Wait up to 30 seconds. Connected means a real poll succeeded. Manually move/cancel your synthetic Google event and watch the automatic chat notification after the next poll. Read-only mode performs no email or Calendar writes; proposal monitoring alone also performs none.

Scopes:

| Scope | Use and actual permission |
| --- | --- |
| `https://www.googleapis.com/auth/gmail.readonly` | Search the classroom label and fetch Subject metadata. Google grants broader mailbox read access; this app restricts its reads. |
| `https://www.googleapis.com/auth/calendar.events.readonly` | Read changes in the configured calendar. The permission is broader than that single calendar; the app restricts requests. |

A browser's existing Google session and Codex connectors are not authentication for this separate app. No browser cookies or connector tokens are copied. The official libraries refresh the app's own local authorization. Testing authorizations can expire (often after seven days for Gmail scopes); rerun consent if needed. A poll error reports Needs attention, with no secret/provider response exposure. To disconnect: stop FastAPI, remove `.local/google-token.json`, and revoke access in Google's connected apps. To switch accounts, use a separate classroom database/label/reference namespace to avoid mixing saved support references across classrooms.

Official references: [Gmail OAuth quickstart](https://developers.google.com/workspace/gmail/api/quickstart/python), [filtered Gmail listing](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/list), [Calendar incremental sync](https://developers.google.com/workspace/calendar/api/guides/sync), [installed-app loopback OAuth](https://developers.google.com/identity/protocols/oauth2/native-app#redirect-uri_loopback).

## Exact counts and local time-window tables

“How many requests I have?” and “How many requests I got?” use exact SQL aggregates. Generic count words are not treated as subject filters. Replies distinguish real Google, demo, and sample origins, with the exact overall total. Explicit status/source/topic constraints are honored (e.g. “How many scheduled demo requests?” or “How many real FastAPI requests?”). Totals are independent of the 20-record detail limit; count-only questions send Gemini no per-request subjects/identities.

Ask “Show a table of all tracked requests from the last 20 minutes,” “last half hour,” or “last hour.” The locally rendered table shows reference, subject, received time, request/workflow status, and the meeting or pending proposal. Time windows use **immutable original Gmail internalDate**, when known, never the latest status update. Older rows use their first observed Gmail activity until an authenticated poll supplies original receive time; fallback rows are explicitly labeled and can make arrival-window counts approximate for those rows. A status change does not make an old email appear newly received.

Tables are rendered locally; Gemini receives only totals, scope and a fallback-time count. The first page shows 20 rows with the exact total and a **Load 20 more saved rows** control. Pages come from the same saved report snapshot so later job changes cannot scramble pagination. “Which jobs are queued / in progress / booked / acknowledged / failed?” and “List upcoming support meetings” query the local job ledger and matched meeting state. Display uses Asia/Kolkata.

For “Who all are invited to SUP-…?”, guest details are fetched only for the matched/created event and rendered locally. They are not copied to Gemini, broad notifications, or saved chat metadata; unrelated events' guests are not fetched. Up to 100 guests are returned with a partial-response marker if Google omits more. Synthetic meetings explicitly report that no real guests were invited.

## Approval-first proposals and booking

Proposal monitoring defaults to **off** for a fresh database. After completing the separate scheduling consent, enable monitoring and use a fresh labeled support email with a new reference. Existing requests are not queued. Approval of a specific live proposal is required before any meeting, invitation or email.

**There is no ingestion-to-booking mode.** A new eligible email can only create an `awaiting_approval` proposal. No Calendar event, invitation, or acknowledgment is sent at receipt/proposal time. After you approve its exact time, the worker checks that slot again, creates one Calendar event inviting only the original actual From sender, and sends one concise Gmail confirmation in the original thread. Combining receipt acknowledgment and confirmed session in one message avoids duplicate mail. No booking failure is represented as a confirmation.

Setup in **Connection settings**:

1. Use **Authorize scheduling & email permissions** and personally approve Google's normal Desktop OAuth consent flow. New authorization is stored separately in `.local/google-automation-token.json`; the original read-only token is preserved. The command-line alternative is `.venv/bin/python -m backend.authorize_google --automation`.
2. Added scopes are `gmail.send`, `calendar.events.owned` (create/manage events only on calendars you own), and `calendar.events.freebusy` (read availability). Existing Gmail/Calendar read scopes remain. No mailbox modify/delete scope or Calendar sharing/admin scope is requested. This app only creates the specifically approved support event; the OAuth capability itself is broader than that one event.
3. Choose an **owned classroom calendar** with `GOOGLE_CALENDAR_ID`. Availability checks include `primary`, the target calendar pinned to that job, and any comma-separated IDs in `GOOGLE_BUSY_CALENDAR_IDS`. All configured calendars must return valid availability. The source read account and scheduling account must match.
4. Enable **new-request proposals**. This starts a persisted activation cutoff, not automatic bookings. Only the first newly tracked labeled message with a valid unique support reference and an original receive timestamp after activation can queue a job. Existing/tracked/booked requests—including previously scheduled requests—are not backfilled on enable, reauthorization, polling, or restart. Emails received while monitoring is paused are not backfilled after re-enabling.
5. New mail produces a saved proposal and a live conversation message: “Shall I schedule…?” Review its specific time, then use **Approve meeting, sender invitation & confirmation** or say “okay, go ahead and set up the meeting” when that proposal is uniquely identified. Multiple candidates require a reference/targeted control. A stale proposal revision cannot be approved. Email content and Gemini output cannot approve anything; deterministic server code handles user actions.
6. Ask “Is tomorrow at 4 p.m. free instead?” or “Check 4 p.m. instead.” A time-only alternate uses the pending proposal's date; ambiguous bare times or dates require clarification. The full 30-minute slot is checked. A free alternate replaces the pending proposal and requires fresh approval. An occupied alternate leaves the prior proposal intact. Neither checking nor selecting an alternate sends or books anything.

Slots are minute-aligned and entirely within **09:00–17:00 India time**, with no weekday restriction. The next slot begins at the earliest future minute that fits, or after the end of an overlapping busy interval. A 30-day search horizon bounds the read; no slot means a visible retry rather than an invented booking. After approval, an occupied or elapsed slot results in a replacement proposal for **new approval**, not silent rescheduling. Google offers no atomic free/busy-and-insert reservation: another calendar client can race the immediate availability check; review any external concurrent changes normally.

A separate **Run safe proposal simulation** exercises proposal, alternate selection, approval, fake booking and fake acknowledgment with no Google writes or credentials. Synthetic messages remain labeled. The original Run demo remains a separate credential-free event-stream exercise. Simulation availability is controlled, not a real Calendar check.

### Durable stages, retries, and uncertainty

`support_jobs` stores `queued → preparing → awaiting_approval → approved → booking → booked → acknowledging → acknowledged`, plus `retry_wait`, `failed`, `booking_uncertain`, and `send_uncertain`. Every meaningful transition is saved with its activity/chat notice before the browser update. Private recipient/threading fields are populated only after approval. Model context exposes safe stage/meeting/error fields, not private delivery metadata.

- Calendar creation uses a deterministic client-supplied event ID and private job marker. A lost insert response reconciles that exact event instead of creating another invitation. A cancelled saved event is never recreated. If an insert's outcome cannot be established, the job checks that ID and requires review rather than blindly creating a second meeting.
- Gmail uses a deterministic RFC Message-ID, original thread ID, subject and reply headers. Before sending/recovery it checks Sent by RFC Message-ID. A crash after send is reconciled. If Gmail's send outcome is ambiguous, the app **does not automatically resend**: it checks Sent later and shows uncertainty. This favors avoiding duplicate mail and may require manual review if the original attempt never reached Gmail. A successful API call/request does not prove delivery to an inbox.
- Transient booking failures retry after five minutes, with a maximum of five failed booking attempts before review. Explicit Gmail rejections may retry after five minutes without recreating the meeting. Missing/invalid sender, missing threading ID, identity conflicts, or revoked access surface a clear failure/pause. No acknowledgment claims success before the meeting exists.
- Pausing monitoring preserves pending work. Clean shutdown waits for an in-flight side-effect step; crashes recover from SQLite stage markers. Approval cannot be replayed to create another event or email. The deterministic state machine owns writes; Gemini has no external mutation tools.

SQLite is the durable memory for the lesson: source receipt keys deduplicate polls, request/job rows checkpoint business progress and approval revisions, activity/chat rows restore live notifications, and read queries power exact counts, time-window tables and job/meeting questions after restart. This extends the teaching deck's process-local background task with a persistent job ledger.

Official references: [Calendar free/busy scopes](https://developers.google.com/workspace/calendar/api/v3/reference/freebusy/query), [Calendar event creation and client event IDs](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert), [Gmail threaded replies](https://developers.google.com/workspace/gmail/api/guides/threads).

## Two streams, one saved conversation

```text
Google read-only polling / saved demo queue
                 ↓
SQLite transaction: receipt + request + activity + chat notification
                 ↓ COMMIT
WebSocket /ws → authoritative saved snapshot → notification bubble

User question → POST /api/chat → read-only SQLite context (if relevant)
                 ↓
Gemini SDK async text stream
                 ↓ each chunk committed to its assistant message
HTTP text/event-stream → growing AI reply (also in WebSocket snapshots)
```

Gemini chunks use a **separate HTTP SSE stream** at `POST /api/chat`; the event WebSocket remains available throughout. FastAPI, not Vite, calls Gemini. Each SSE packet contains the current saved assistant message at a monotonic revision. The browser merges by stable message ID and revision, never by “append to the last bubble.” This prevents a live notification from interrupting/absorbing reply text and prevents double-appends when SSE and WebSocket race.

Messages, replies and notifications are stored in `chat_messages`. An event's ID is `event:<activity sequence>`; repeated receipts and migration cannot create a second notification. User/assistant IDs derive from a client request UUID; retries with the same UUID replay the saved answer. Gemini does not rerun for duplicate requests. Snapshots restore the **latest 200 messages**; older messages remain in SQLite. At most two Gemini replies run concurrently. Chat is shared on this one local teaching instance, not per-user/multi-tenant.

A reply continues in a managed server task if its initiating browser reloads/disconnects. Its committed partial text recovers through WebSocket snapshots. Shutdown cancels work and marks an unfinished reply interrupted; send the question again to generate a new answer. Errors preserve partial text and show a clear notice. A reply has a 90-second application timeout and 45-second SDK request timeout. Text is rendered as escaped plain text; model output cannot execute HTML.

Gmail re-scans the dedicated label with pagination and deduplicates message IDs. Calendar saves and uses `nextSyncToken`, including deletions; 410 restarts the full scan. Checkpoints advance only after changes commit. A full scan cannot reconstruct deleted events Google no longer returns. Demo steps are saved in `pending_demo` before HTTP 202 and resume after restart; a crash after apply and before queue deletion safely replays the same receipt.

## Verify the lesson

```bash
cd live-student-support-dashboard
.venv/bin/python -m pytest backend/tests -q
cd frontend
npm run build
```

The tests stub Gemini for credential-free verification: stream packet boundaries, event arrival during a reply, committed text, idempotent request IDs, interrupted reply recovery, relevant-record filtering, timezone formatting, metadata-only Google reads, duplicate receipts, out-of-order events, and durable demo continuation. They do not claim live Gemini/Google access. See [VERIFICATION.md](VERIFICATION.md) for actual browser/provider checks.

In class: ask a general question, ask about FastAPI tutoring, run the demo while a reply streams, reload, restart FastAPI with the chat open, and replay the sample twice. Then manually change a matching real Google event if you have prepared one and wait for its chat notification.

Read the code in this order: `backend/store.py` (commit and message identity), `backend/main.py` (workers, WebSocket, HTTP stream), `backend/chat.py` (lookup, privacy, Gemini), `backend/google_sync.py` (read-only polling), `frontend/src/main.jsx` (message/revision merge).

## Local data and boundaries

Run **one FastAPI worker**, bound to `127.0.0.1`. This is a local teaching app without login; do not expose it publicly. Multiple workers would require a shared broadcast channel and generation/worker coordination. Browser mutations and WebSockets reject unrelated origins; hosts are restricted to localhost/127.0.0.1. Local non-browser clients can call the simulator.

SQLite retains support references, truncated subjects, original Gmail receive time where available (or a labeled first-observed fallback), statuses, tutoring dates, source IDs/versions, activity, checkpoints, demo queue, private scheduling jobs, saved report snapshots, questions and assistant text (including partial/failed replies and grounding metadata). Chat text can itself contain personal data; use synthetic classroom data. OAuth tokens are separate private files, never SQLite/browser/model input. Client, token, `.env`, database and dependency/build folders are ignored; token writes are atomic and owner-only. Gemini requests are processed by Google's Gemini service under the account's terms; this app is not an offline model.

Retention is manual. With FastAPI stopped, remove only `.local/support.sqlite3` and any `-wal`/`-shm` companions to clear all records/chat/pending demos/checkpoints. Reload the browser after a reset. To clear local credentials too, remove this app's `.local` folder while stopped and revoke Google consent separately. Local credentials and saved classroom history are not included in the repository.
