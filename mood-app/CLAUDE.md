# Moodnotes — notes for Claude

A teaching project: a notes app whose chatbot calls 17 real tools against a SQLite database. It is
used to teach people who are **new to Python**.

## Setting the project up

**Read [SETUP.md](SETUP.md) and follow it.** It has the full end-to-end sequence, the verification
steps, and a troubleshooting table. The short version:

```bash
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env          # then paste an OpenAI key into it
cd ../frontend && npm install
```

Then two terminals:

```bash
cd backend && .venv/bin/uvicorn main:app --reload --port 8000
```

```bash
cd frontend && npm run dev
```

## Things that will bite you

- **Python must be 3.10 or newer.** The code uses `int | None`, which is a syntax error on 3.9.
  macOS ships 3.9, so check `python3 --version` before creating the venv.
- **Uvicorn must be started from inside `backend/`.** Modules import each other by plain name
  (`from models import ...`), so any other working directory gives `ModuleNotFoundError`.
- **`backend/.env` holds a real API key.** Never print it, commit it, or move it into frontend
  code. It is gitignored — leave it that way.
- **No key is not a bug.** Without one, everything works except the chatbot, which replies asking
  for a key. That is the intended behaviour.
- **`.env` is read once at startup.** After editing it, restart the backend.

## House style — this matters here

The code is the teaching material, so readability beats cleverness:

- Every file starts with a one-line comment saying what it does, in plain English.
- Keep files under roughly 150–200 lines. Split rather than let one grow.
- Prefer a well-known library over hand-rolled logic. No manual string parsing or regex where a
  package will do.
- Factor repetition into one shared place — see `crud.py` and `routers/simple_crud.py`, which is
  why categories, tags and moods are three lines each in `main.py`.
- Avoid clever one-liners that a beginner has to decode. Write the value out explicitly.

## Layout

```
backend/       FastAPI + SQLModel + SQLite. The agent lives in agent.py, its tools in tools/
frontend/      Vite + React. State is all in useNotesApp.js
```

This project sits inside the `bia-batch-july` course repo. The slide decks are shared across the
course and live one level up, in `../presentations/` — do not move them back in here.

`SETUP.md` section 7 has a file-by-file table for both halves.

## Adding a chatbot tool

Write the function in the right file under `backend/tools/`, put `@function_tool` above it with a
clear docstring — the model reads that docstring to decide when to call it — then add it to
`ALL_TOOLS` in `backend/tools/__init__.py`.

## Verifying a change

Do not assume it works. `SETUP.md` section 5 has concrete checks. The quickest end-to-end one:

```bash
curl -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" \
  -d '{"message":"How many times was I happy?","history":[]}'
```

A correct response has both `reply` and `trace`, and `trace.steps` shows the agent asking for
`count_notes_by_mood`, the code returning counts, then the model writing the answer.
