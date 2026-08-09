# Moodnotes

A small notes app with **notes, categories, tags and moods**, plus a chatbot that can read
and change your notes by calling real API tools.

- **Backend** — Python, FastAPI, SQLite (via SQLModel), OpenAI Agents SDK
- **Frontend** — Vite + React

---

## Run it

**First time here?** Read [SETUP.md](SETUP.md) — it installs the packages, and has verification
and troubleshooting steps. Once that is done, you need two terminals: one for the backend, one
for the frontend.

**1. Backend**

```bash
cd backend && .venv/bin/uvicorn main:app --reload --port 8000
```

Open http://127.0.0.1:8000/docs to try the API by hand.

**2. Frontend**

```bash
cd frontend && npm run dev
```

Open the address it prints (usually http://localhost:5173).

**3. The chatbot key**

Open `backend/.env` and paste your OpenAI key after the `=` sign:

```
OPENAI_API_KEY=sk-...
```

Then restart the backend. Notes, categories, tags and moods all work without a key —
only the chatbot needs it.

---

## What is where

### Backend (`backend/`)

| File | What it does |
| --- | --- |
| `main.py` | Starts the app and plugs in all the routes |
| `database.py` | Connects to the SQLite file `notes.db` |
| `models.py` | The four tables: Note, Category, Tag, Mood |
| `schemas.py` | The shape of data going in and out of the API |
| `crud.py` | List / get / create / update / delete, written once and reused |
| `cleanup.py` | Frees notes from a category, tag or mood that gets deleted |
| `seed.py` | Puts starter data in the database on the first run |
| `routers/simple_crud.py` | Builds the 4 routes for categories, tags and moods |
| `routers/notes.py` | The note routes, including filtering and search |
| `routers/chat.py` | The `/chat` and `/explain` routes |
| `agent.py` | The chatbot: its instructions and its tools |
| `agent_trace.py` | Records what was sent to the LLM and which tools ran |
| `explainer.py` | A second, tool-free agent that explains a trace to students |
| `tools/` | The 17 tools the chatbot can use |

### Frontend (`frontend/src/`)

| File | What it does |
| --- | --- |
| `App.jsx` | The three column screen |
| `api.js` | One small wrapper around `fetch` |
| `useNotesApp.js` | Holds all the data and the filters in one place |
| `components/Sidebar.jsx` | Search box and the filter chips |
| `components/NoteGrid.jsx` | The note cards and the "New note" button |
| `components/NoteEditor.jsx` | The popup for writing a note |
| `components/ManagePanel.jsx` | Add / rename / recolour / delete for all three lists |
| `components/Chat.jsx` | The chatbot column |
| `components/TracePanel.jsx` | The 👁 popup that shows how an answer was made |
| `components/ui.jsx` | Chip, Section and Modal building blocks |
| `styles/` | The look of the app, split by area |

---

## The chatbot tools

The agent has **17 tools**, one for each thing you can do:

- **Notes** — `list_notes`, `count_notes_by_mood`, `create_note`, `update_note`, `delete_note`
- **Categories** — `list_categories`, `create_category`, `update_category`, `delete_category`
- **Tags** — `list_tags`, `create_tag`, `update_tag`, `delete_tag`
- **Moods** — `list_moods`, `create_mood`, `update_mood`, `delete_mood`

Each one is a plain Python function with `@function_tool` written above it, for example:

```python
@function_tool
def list_categories() -> list[dict]:
    """List every category the user has."""
    with new_session() as session:
        return [c.model_dump() for c in crud.list_all(session, Category)]
```

---

## The 👁 button — for teaching

Every answer from the chatbot has a small eye button next to it. Click it to open a popup that
shows exactly how that answer was made, in four parts:

1. **What we sent to the LLM** — the instructions, the earlier messages, the new question, and the
   names of all 17 tools. This is the part students usually miss: the *whole* thing is sent again
   with every single question. The LLM has no memory of its own.
2. **What happened, step by step** — a badge for each move, so it is obvious who did what:
   `LLM` asked for a tool → `OUR PYTHON CODE` ran it and sent the data back → `LLM` wrote the
   answer. The arguments and the tool's result are shown as formatted JSON.
3. **The conversation the LLM now has** — the full JSON, plus how many calls to the LLM it took
   and how many tokens were used. Usually **two** calls: one to pick the tool, one to write the
   answer after seeing the result.
4. **The same thing, explained in simple words** — a second agent (`explainer.py`) reads the trace
   and describes it in plain English.

The point students should take away: the LLM never touches the database. It can only ask for a
tool *by name*, our Python code runs it, and we hand the result back.

### Things to ask it

- "What categories do I have?"
- "Add a category called Travel"
- "Delete the Travel category"
- "How many times was I happy?"
- "Show me the notes where I was happy"
- "Write a note called Gym day, mood Excited, tag it goals"

---

## Presentations

The decks are shared across the whole course, so they live one level up in
[`../presentations/`](../presentations) rather than in this folder. Open
`../presentations/index.html` in a browser — no server, no install.

The deck for this project is **`agent-architecture.html`** (session two): what an agent really is,
workflow vs autonomous, the core loop, tools, context and memory, delegation, safety, state,
evaluation, cost, and what to build first.

---

## Starting over

Delete `backend/notes.db` and restart the backend. The starter notes come back.
