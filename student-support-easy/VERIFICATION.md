# Verification

## Reproduce without Google writes

From this app folder, after installing `requirements.lock.txt`:

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q backend
cd frontend
npm ci
npm run build
```

The automated tests use temporary SQLite files and fake Google clients. They check subject matching without labels, old/automatic message filtering, saved state after restart, business-hour availability, skipping previously handled messages, and stopping after failed sends. They send no real email or Calendar invitations.

Prior local integration checks verified WebSocket sample updates in the chat and table, simultaneous Gemini streaming and notifications, saved data after restart, and distinct request counts for identical subjects. An explicitly authorized live classroom test also exercised email receipt, meeting creation, confirmation sending, and the saved done status. Specific message subjects, meeting times, account details, screenshots, and local conversation/data files are omitted from publication.

The final workflow is intentionally simple: show the request, create/save the meeting, send the confirmation. Every recorded email is skipped on later polls, even after interruption. There is no automatic recovery; inspect unfinished requests manually.

Publication checks are run in a clean checkout without local credentials. No Google writes or test emails are initiated during publication.

## Publication results — 22 November 2026

- Fresh Python 3.12 install from the platform-aware lockfile passed; dependency compatibility check passed.
- All **8 automated tests passed**, including environment/file configuration precedence and the missing-key response.
- Python compilation passed.
- `npm ci` and the React/Vite production build passed; npm reported zero known vulnerabilities.
- Public configuration is a placeholder `.env.example`; local credentials, live test details, screenshots, databases, conversations, dependencies, and build outputs are excluded.
