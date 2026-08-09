# Setup — from a fresh clone to a running app

This file is written so that a person **or an AI coding agent** can set this project up end to end
without asking anyone questions. Follow it top to bottom.

**What you get at the end:** a notes app running at `http://localhost:5173`, talking to a Python
API at `http://127.0.0.1:8000`, with a chatbot that calls 17 real tools against a SQLite database.

All the commands below are run from **this folder** (`mood-app/`) unless a step says otherwise.

---

## 0. Requirements

| Need | Minimum | Check it with |
| --- | --- | --- |
| Python | **3.10 or newer** | `python3 --version` |
| Node.js | **18 or newer** | `node --version` |
| npm | any recent | `npm --version` |

> **Python 3.10 is a hard requirement, not a suggestion.** The code uses the modern
> `int | None` type syntax, which is a syntax error on Python 3.9 and older. macOS ships with
> Python 3.9, so `python3` on a Mac is very often too old. Check the version *before* you start.

**If `python3 --version` is older than 3.10**, install a newer one and use its full path in Step 1:

```bash
# macOS
brew install python@3.12

# Ubuntu / Debian
sudo apt update && sudo apt install python3.12 python3.12-venv

# Or, on any platform, with uv (https://docs.astral.sh/uv/)
uv python install 3.12
```

---

## 1. Backend — virtual environment and packages

The virtual environment goes inside `backend/`:

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

If your default `python3` was too old, swap the first command for the newer one you installed,
for example `python3.12 -m venv .venv` or `/opt/homebrew/bin/python3.12 -m venv .venv`.

This installs FastAPI, Uvicorn, SQLModel, the OpenAI Agents SDK and python-dotenv.

> **Windows note:** the venv puts executables in `.venv\Scripts\` instead of `.venv/bin/`.
> Use `.venv\Scripts\python -m pip ...` and `.venv\Scripts\uvicorn ...` throughout this file.

---

## 2. Backend — the API key

The chatbot needs an OpenAI API key. Everything else (notes, categories, tags, moods) works
without one.

```bash
cp .env.example .env
```

Then open `backend/.env` and paste your key after the `=`:

```
OPENAI_API_KEY=sk-your-key-here
```

**Rules for an AI agent working on this repo:**

- **Never** print, echo, log or commit the contents of `.env`. It is already in `.gitignore`.
- **Never** put the key in frontend code — the frontend runs in the browser, where anyone can read it.
- If no key is present the app still starts. The chatbot simply replies asking for one, which is
  the correct behaviour. Do not treat that reply as a bug.

---

## 3. Frontend — packages

```bash
cd frontend
npm install
```

---

## 4. Run it

You need **two terminals**, both left running.

**Terminal 1 — backend.** It must be started from inside `backend/`, because the modules import
each other by plain name (`from models import ...`):

```bash
cd backend && .venv/bin/uvicorn main:app --reload --port 8000
```

**Terminal 2 — frontend:**

```bash
cd frontend && npm run dev
```

Open the address Vite prints, normally <http://localhost:5173>.

On the very first backend start, `backend/notes.db` is created and filled with 5 moods,
3 categories, 3 tags and 6 example notes. That happens once; after that your own data is kept.

---

## 5. Verify it actually works

Run these checks rather than assuming. Every one should pass.

**The API is up and seeded:**

```bash
curl -s http://127.0.0.1:8000/categories
```

Expect three categories: Personal, Work, Ideas.

**Notes come back with their mood, category and tags joined in:**

```bash
curl -s http://127.0.0.1:8000/notes
```

**Creating and deleting works:**

```bash
curl -s -X POST http://127.0.0.1:8000/categories \
  -H "Content-Type: application/json" \
  -d '{"name":"Travel","color":"#cc785c"}'
```

Note the `id` that comes back, then remove it again:

```bash
curl -s -X DELETE http://127.0.0.1:8000/categories/<id>
```

**The interactive API docs load:** open <http://127.0.0.1:8000/docs>.

**The chatbot and its tools work** (needs the API key from Step 2):

```bash
curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"How many times was I happy?","history":[]}'
```

A correct response contains both a `reply` and a `trace`. Inside `trace.steps` you should see the
agent asking for the `count_notes_by_mood` tool, our code returning the counts, then the model
writing the answer.

**In the browser:** the notes grid shows the example notes, clicking a mood chip in the left
sidebar filters them, and each chatbot answer has a 👁 button that opens the full trace.

---

## 6. When something breaks

| Symptom | Cause and fix |
| --- | --- |
| `TypeError: unsupported operand type(s) for \|` on startup | Python is older than 3.10. Rebuild the venv with a newer Python (Step 0). |
| `ModuleNotFoundError: No module named 'models'` | Uvicorn was started from the wrong folder. It must run from inside `backend/`. |
| `ImportError: No module named fastapi` | You used the system Python instead of the venv. Use `.venv/bin/uvicorn`, not bare `uvicorn`. |
| Frontend loads but no notes, console shows failed fetches | The backend is not running, or not on port 8000. The URL is set in `frontend/src/api.js`. |
| Chatbot replies "Please add your OPENAI_API_KEY…" | Expected with no key. Add it to `backend/.env` and restart the backend — `.env` is only read at startup. |
| Chatbot returns a 401 or auth error | The key is present but wrong, expired, or has no credit. |
| `Port 5173 is already in use` | Something else has it — often the `simple_agent_chatbot` frontend. Stop it, or run `npm run dev -- --port 5174`. |
| Want to start over with fresh example data | Stop the backend, delete `backend/notes.db`, start it again. **This deletes all your notes.** |

---

## 7. How the code is laid out

Useful if you are changing something rather than just running it. Every file opens with a
one-line comment saying what it does, and no file is longer than about 160 lines.

### Backend (`backend/`)

| File | Role |
| --- | --- |
| `main.py` | Creates the tables, seeds them, mounts every route |
| `database.py` | The SQLite connection and the per-request session |
| `models.py` | The four tables: Note, Category, Tag, Mood |
| `schemas.py` | What the browser sends and receives |
| `crud.py` | list / get / create / update / delete, written once and shared |
| `cleanup.py` | Frees notes from a category, tag or mood that gets deleted |
| `seed.py` | The starter data, created only on an empty database |
| `routers/simple_crud.py` | A factory that builds 4 routes for any simple table |
| `routers/notes.py` | Note routes, including filtering and search |
| `routers/chat.py` | `POST /chat` and `POST /explain` |
| `agent.py` | The chatbot: its instructions, model and tool list |
| `agent_trace.py` | Records what went to the LLM and which tools ran |
| `explainer.py` | A second, tool-free agent that explains a trace |
| `tools/` | The 17 `@function_tool` functions the chatbot can call |

Categories, tags and moods share one router factory, so adding a similar table is three lines in
`main.py`. Notes have their own router because they carry a list of tags.

### Frontend (`frontend/src/`)

| File | Role |
| --- | --- |
| `App.jsx` | The three-column layout |
| `useNotesApp.js` | All the data and filters, in one place |
| `api.js` | A small wrapper around `fetch`. The backend URL lives here |
| `components/Sidebar.jsx` | Search box and filter chips |
| `components/NoteGrid.jsx`, `NoteCard.jsx` | The notes |
| `components/NoteEditor.jsx` | The write/edit popup |
| `components/ManagePanel.jsx` | Add / rename / recolour / delete for all three lists |
| `components/Chat.jsx` | The assistant column |
| `components/TracePanel.jsx` | The 👁 popup showing how an answer was made |
| `styles/` | Plain CSS, split by area |

### The slides

The decks are not in this folder — they are shared across the whole course and live in
[`../presentations/`](../presentations). The one for this project is `agent-architecture.html`.
No build step: open `../presentations/index.html` in a browser.

---

## 8. Things to know before changing code

- **Adding a Python package:** add it to `backend/requirements.txt` and install it into the venv.
- **Adding a chatbot tool:** write the function in the right file under `backend/tools/`, put
  `@function_tool` above it with a clear docstring (the model reads that docstring to decide when
  to use it), then add it to `ALL_TOOLS` in `backend/tools/__init__.py`.
- **Changing a table:** SQLite will not migrate itself here. After editing `models.py`, delete
  `backend/notes.db` and restart so the new shape is created.
- **The `.env` file must never be committed.** It is in `.gitignore`; keep it that way.
- **Keep files small and commented.** This is teaching material — clarity beats cleverness.
