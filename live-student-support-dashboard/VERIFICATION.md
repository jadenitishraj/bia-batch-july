# Verification

This publication includes application source, automated tests, dependency lockfiles, synthetic replay payloads, configuration placeholders, and documentation. OAuth files, keys, local databases, conversations, virtual environments, and build outputs are excluded.

## Reproduce the credential-free checks

From this app folder:

```bash
uv venv --python 3.12 .venv
uv pip install -r backend/requirements.lock.txt
.venv/bin/python -m pytest backend/tests -q
.venv/bin/python -m compileall -q backend scripts
cd frontend
npm ci
npm run build
```

The automated tests use synthetic records and stubbed Google/Gemini services. They cover saved source receipts and duplicate handling, Calendar ordering and cancellations, durable demo continuation, chat streaming and interruptions, snapshot/message merging, read-only classroom context, exact counts and local reports, contextual follow-ups, revision-bound proposal approval, availability checks, and uncertain external writes. They send no real invitations or mail.

## Prior local integration checks

Local browser checks verified incremental Gemini text, separate incoming event notifications during a reply, saved-conversation recovery after restart, and reconnect without duplicate message IDs. Authorized Gmail/Calendar reads and Calendar availability were also exercised locally. Synthetic proposal simulations exercised alternate slots, explicit approval, booking, and acknowledgment without Google writes.

These observations do not prove that a new installation has valid Google consent, Gemini access, or working live email delivery. Follow the README setup and use synthetic classroom data for your own live test. Specific account details, conversation history, OAuth project identifiers, and live support records are intentionally omitted.

## Publication checks

Checked on 22 November 2026 in a clean checkout based on the remote default branch:

- Python 3.12: all **27 backend tests passed**, with one upstream Starlette/AnyIO deprecation warning.
- Python compilation: passed for backend and sample sender.
- Fresh install from the regenerated Python lockfile: passed; `uv pip check` found no incompatible packages. The OAuth helper pin was updated to 1.5.0 to support the authentication version required by Gemini.
- `npm ci`: succeeded; npm reported zero known vulnerabilities.
- React/Vite production build: passed.
- Publication includes 26 app files; no environment file, OAuth JSON/token, local database, conversation data, dependency folder, or build output is staged. Public fixtures use synthetic references and example addresses.

No local credentials or dataset are needed to reproduce these automated checks.
