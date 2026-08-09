# Setup — from a fresh clone to a running agent

This file is written so that a person **or an AI coding agent** can set this project up end to end
without asking anyone questions. Follow it top to bottom.

**What you get at the end:** a chat screen at `http://localhost:5173`, talking to a Python API at
`http://localhost:8001`, with an agent that has **15 tools** — maths, a searchable document
corpus, memory it can write to, and small text helpers.

All the commands below are run from **this folder** (`simple_agent_chatbot/`) unless a step says
otherwise.

---

## 0. Requirements

| Need | Minimum | Check it with |
| --- | --- | --- |
| Python | **3.10 or newer** | `python3 --version` |
| Node.js | **18 or newer** | `node --version` |
| npm | any recent | `npm --version` |

> **Python 3.10 is a hard requirement, not a suggestion.** LangChain will not install on 3.9.
> macOS ships with Python 3.9, so `python3` on a Mac is very often too old. Check the version
> *before* you start.

**If `python3 --version` is older than 3.10**, install a newer one and use its name in Step 1:

```bash
# macOS
brew install python@3.12

# Ubuntu / Debian
sudo apt update && sudo apt install python3.12 python3.12-venv

# Or, on any platform, with uv (https://docs.astral.sh/uv/)
uv python install 3.12
```

---

## 1. Python — virtual environment and packages

The virtual environment goes in **this folder**, not in `backend/`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r backend/requirements.txt
```

If your default `python3` was too old, swap the first command for the newer one you installed,
for example `python3.12 -m venv .venv`.

This installs FastAPI, Uvicorn, LangChain, langchain-openai and python-dotenv.

> **Windows note:** the venv puts executables in `.venv\Scripts\` instead of `.venv/bin/`.
> Use `.venv\Scripts\python -m pip ...` and `.venv\Scripts\uvicorn ...` throughout this file.

---

## 2. The API key

The agent needs an OpenAI key. There is no offline mode — without a key nothing answers.

```bash
cp .env.example .env
```

Then open `.env` and paste your key after the `=`:

```
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

`OPENAI_MODEL` is optional — leave it as `gpt-4o-mini`, which is cheap and calls tools well.

**Rules for an AI agent working on this repo:**

- **Never** print, echo, log or commit the contents of `.env`. It is already in `.gitignore`.
- **Never** put the key in frontend code — the frontend runs in the browser, where anyone can
  read it.
- Do not invent a key or take one from anywhere else. If `.env` is missing, stop and ask the
  person to create it.
- `.env` is read once at startup. After editing it, restart the backend.

---

## 3. Frontend — packages

```bash
cd frontend && npm install
```

---

## 4. Try the agent in the terminal first

Do this before touching the API or React. Nothing is hidden here — you type a question and every
phase of the agent loop is printed.

```bash
cd backend && ../.venv/bin/python test_agent.py
```

It prints all 15 tools, then waits. Try:

```
what is 12 times 8?
how much does the Team plan cost?
remember that my name is Nitish
```

Type `quit` to stop.

---

## 5. Run the app

You need **two terminals**, both left running.

**Terminal 1 — backend.** It must be started from inside `backend/`, because the modules import
each other by plain name (`import agent`, `from tools.registry import ...`):

```bash
cd backend && ../.venv/bin/uvicorn main:app --reload --port 8001
```

**Terminal 2 — frontend:**

```bash
cd frontend && npm run dev
```

Open the address Vite prints, normally <http://localhost:5173>.

> The port numbers matter. React is hard-coded to call `http://localhost:8001` — it is set at the
> top of `frontend/src/App.jsx`. If you move the backend to another port, change it there too.

---

## 6. Verify it actually works

Run these checks rather than assuming. Every one should pass.

**The API is up and the registry loaded:**

```bash
curl -s http://localhost:8001/
```

Expect `{"status":"ok","tools":15}`.

**Every tool is registered with a description the model can read:**

```bash
curl -s http://localhost:8001/tools
```

**A tool actually runs** — this one needs the API key:

```bash
curl -s -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"what is 12 times 8?","session_id":"test"}'
```

A correct response has an `answer` of 96, and `steps` showing the model asking for `multiply`,
our Python returning `96.0`, then the model writing the sentence.

**It answers from our own documents, not from general knowledge:**

```bash
curl -s -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"how much does the Team plan cost?","session_id":"test"}'
```

Expect 30 dollars per user per month, taken from `data/corpus.json` via the
`search_knowledge_base` tool.

**Long term memory survives a restart:**

```bash
curl -s -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"remember that my favourite colour is blue","session_id":"test"}'

curl -s http://localhost:8001/memory/long-term
```

The fact is now in `data/long_term_memory.json`. Stop the backend, start it again, and ask
"what is my favourite colour?" — it still knows.

**Short term memory is per conversation:** ask a follow-up like "and multiply that by 2" in the
same `session_id`. It knows what "that" was. Change the `session_id` and it does not.

**The interactive API docs load:** open <http://localhost:8001/docs>.

**In the browser:** send a message at <http://localhost:5173> and the steps of the agent run
appear alongside the answer.

---

## 7. When something breaks

| Symptom | Cause and fix |
| --- | --- |
| `ERROR: Could not find a version that satisfies langchain` | Python is older than 3.10. Rebuild the venv with a newer Python (Step 0). |
| `ModuleNotFoundError: No module named 'agent'` | Uvicorn was started from the wrong folder. It must run from inside `backend/`. |
| `ModuleNotFoundError: No module named 'fastapi'` | You used the system Python instead of the venv. Use `../.venv/bin/uvicorn`, not bare `uvicorn`. |
| `openai.AuthenticationError` / 401 | The key in `.env` is missing, wrong, expired, or has no credit. |
| `RateLimitError` / 429 | Out of credit, or too many requests. Check your OpenAI billing page. |
| Chat screen loads but every message fails | The backend is not running, or not on port 8001. The URL is at the top of `frontend/src/App.jsx`. |
| `Port 5173 is already in use` | Something else has it — often the `mood-app` frontend. Stop it, or run `npm run dev -- --port 5174`. |
| `Port 8001 is already in use` | An older backend is still running. Stop it, or use another port and update `App.jsx`. |
| The agent answers from general knowledge instead of our documents | It did not call `search_knowledge_base`. Ask a question that clearly matches `data/corpus.json`, or sharpen the system prompt in `backend/prompts.py`. |
| Want to wipe what it remembers | Delete the contents of `data/long_term_memory.json` (leave `[]` or `{}` as the file expects), or ask it to "forget everything". |

---

## 8. How the code is laid out

Every file opens with a comment saying what it does. Read them in this order — it is the order
the ideas build in.

```
backend/
├── prompts.py             The system prompt — the agent's rules
├── tools/
│   ├── math_tools.py      add, subtract, multiply, divide, percent_of
│   ├── data_tools.py      search our JSON corpus, like a small web search
│   ├── memory_tools.py    remember_fact, recall_facts, forget_everything
│   ├── text_tools.py      time, word count, uppercase, reverse
│   └── registry.py        THE TOOL REGISTRY — all 15 tools in one list
├── agent.py               The agent = model + tools + system prompt. The loop lives here
├── trace.py               Prints every phase of a run, so the loop is visible
├── short_term_memory.py   The current conversation, kept in RAM
├── long_term_memory.py    Facts saved forever, in a JSON file
├── test_agent.py          Run the agent in the terminal, no API and no React
└── main.py                FastAPI — the door React knocks on

data/
├── corpus.json            The documents the agent searches
└── long_term_memory.json  What it has remembered. This file grows as you chat

frontend/src/App.jsx       The whole chat screen, in one file
```

**The one idea to take away:** an agent is a growing list of messages. The model never runs your
code — it only says *which* function it wants and with *which* arguments. LangChain runs the
Python function and puts the result back into the list as a `ToolMessage`. Then the model reads
it and continues. `backend/trace.py` prints exactly that, one phase at a time.

The matching slide deck is
[`presentations/simple-agent-architecture.html`](../presentations/simple-agent-architecture.html).

---

## 9. Things to know before changing code

- **Adding a tool:** write the function in the right file under `backend/tools/` with `@tool`
  above it and a clear docstring — *the model reads that docstring to decide when to call it* —
  then add its name to `ALL_TOOLS` in `backend/tools/registry.py`. Nothing else to change.
- **Adding a Python package:** add it to `backend/requirements.txt` and install it into the venv.
- **Changing what it knows:** edit `data/corpus.json`. Each entry needs `id`, `title`, `topic`
  and `text`.
- **Changing how it behaves:** edit the system prompt in `backend/prompts.py`.
- **The `.env` file must never be committed.** It is in `.gitignore`; keep it that way.
- **Keep files small and commented.** This is teaching material — clarity beats cleverness.
