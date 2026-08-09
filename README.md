# BIA — Generative & Agentic AI Development (July batch)

Everything from the course in one place: the slide decks, the Colab notebook, and the two
projects we build together.

```bash
git clone https://github.com/jadenitishraj/bia-batch-july.git
cd bia-batch-july
```

---

## What is where

| Folder | What it is | Do you need to install anything? |
| --- | --- | --- |
| [`presentations/`](presentations) | All five slide decks, plus a landing page linking them | No — plain HTML, open in a browser |
| [`google-collab-notebooks/`](google-collab-notebooks) | Python notebooks for Google Colab | No — upload to Colab, runs in the cloud |
| [`mood-app/`](mood-app) | Notes app + chatbot with 17 real tools (session two) | Yes — Python and Node. See [mood-app/SETUP.md](mood-app/SETUP.md) |
| [`simple_agent_chatbot/`](simple_agent_chatbot) | The agent loop on its own, nothing else (session three) | Yes — Python and Node. See [simple_agent_chatbot/SETUP.md](simple_agent_chatbot/SETUP.md) |

---

## 1. The slides — start here

Open [`presentations/index.html`](presentations/index.html) in your browser. That page links to
all five decks. Inside a deck, use the **Slides** menu at the top or just press the arrow keys.

| Deck | For | Covers |
| --- | --- | --- |
| `web-foundations.html` | Start here if you have never written code | HTML, CSS, JavaScript, JSON, what a server is, APIs, GET/POST/PUT/DELETE, FastAPI, databases and SQL |
| `genai-foundations.html` | Session one | Classical ML vs deep learning vs Gen AI, the timeline, diffusion vs autoregressive, model licences, HuggingFace, running a model locally with Ollama |
| `agent-architecture.html` | Session two | What an agent really is, workflow vs autonomous, the core loop, tools, context, memory, safety, evaluation, cost |
| `simple-agent-architecture.html` | Session three | The `simple_agent_chatbot` project explained file by file — system prompt, tools, the registry, memory, FastAPI, React |
| `mini-gpt.html` | Session four | Inside the model: characters to vectors, self-attention, residuals, softmax, sampling, training |

Nothing to install. They are single HTML files.

---

## 2. The notebook

[`google-collab-notebooks/Complete_Python_Essentials.ipynb`](google-collab-notebooks) — the Python
refresher.

Go to <https://colab.research.google.com>, choose **File → Upload notebook**, pick the `.ipynb`
file, and run the cells top to bottom with **Shift+Enter**. Nothing to install on your laptop.

---

## 3. The two projects

Both are built the same way — a **Python FastAPI backend** and a **React frontend** — so once you
have run one, the other is familiar.

|  | `mood-app` | `simple_agent_chatbot` |
| --- | --- | --- |
| What it teaches | An agent working on a real database | The agent loop itself, with nothing around it |
| Agent library | OpenAI Agents SDK | LangChain |
| Storage | SQLite database | JSON files |
| Tools the agent has | 17 (notes, categories, tags, moods) | Maths, search, memory, text |
| Backend port | **8000** | **8001** |
| Frontend port | 5173 | 5173 |
| Full instructions | [mood-app/SETUP.md](mood-app/SETUP.md) | [simple_agent_chatbot/SETUP.md](simple_agent_chatbot/SETUP.md) |

> Both frontends want port **5173**, so run one project at a time. If you really want both at
> once, start the second with `npm run dev -- --port 5174`.

### The short version

Each project needs **three things**: Python packages, an OpenAI key, and Node packages. Then you
run two terminals — backend and frontend.

**mood-app**

```bash
cd mood-app/backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

```bash
cd mood-app/frontend && npm install
```

Put your key in `mood-app/backend/.env`, then two terminals:

```bash
cd mood-app/backend && .venv/bin/uvicorn main:app --reload --port 8000
```

```bash
cd mood-app/frontend && npm run dev
```

**simple_agent_chatbot**

```bash
cd simple_agent_chatbot && python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt
```

```bash
cd simple_agent_chatbot/frontend && npm install
```

Put your key in `simple_agent_chatbot/.env`, then two terminals:

```bash
cd simple_agent_chatbot/backend && ../.venv/bin/uvicorn main:app --reload --port 8001
```

```bash
cd simple_agent_chatbot/frontend && npm run dev
```

Open <http://localhost:5173> either way.

If any of that goes wrong, do not guess — the `SETUP.md` in the project folder has a
troubleshooting table with the exact error messages.

---

## 4. Letting Claude Code set it up for you

Both projects have a `SETUP.md` written so an AI coding agent can follow it without asking you
questions. Open the folder in Claude Code and say:

```
Read simple_agent_chatbot/SETUP.md and set the project up. Then run the verification
steps in it and tell me what passed.
```

Two things it cannot do for you:

- **Your API key.** Claude will not type a key it has not been given. Create the `.env` file and
  paste the key in yourself.
- **Installing Python or Node** if they are missing — that usually needs your password.

---

## 5. Before you start — what you need installed

| Need | Minimum | Check with |
| --- | --- | --- |
| Python | **3.10 or newer** | `python3 --version` |
| Node.js | **18 or newer** | `node --version` |
| An OpenAI API key | any | <https://platform.openai.com/api-keys> |

> **macOS ships Python 3.9, which is too old for both projects.** Check the version before you
> begin. `brew install python@3.12` fixes it.

The API key is only needed for the chatbot parts. In `mood-app` everything else — writing notes,
categories, tags, moods — works fine without one.

---

## 6. The rule about your API key

Your key is like a password with your credit card behind it.

- It goes in a `.env` file. Nowhere else.
- `.env` is in `.gitignore`. **Never commit it, never paste it into a message, never put it in
  frontend code** — the frontend runs inside the browser, where anyone can read it.
- If you think a key has leaked, delete it at <https://platform.openai.com/api-keys> and make a
  new one.

---

## 7. Folder map

```
bia-batch-july/
├── presentations/              5 HTML decks + index.html landing page
├── google-collab-notebooks/    Colab notebooks (.ipynb)
├── mood-app/                   Notes app + 17-tool chatbot
│   ├── backend/                FastAPI, SQLModel, SQLite, OpenAI Agents SDK
│   ├── frontend/               Vite + React
│   └── SETUP.md                Full setup, verification, troubleshooting
└── simple_agent_chatbot/       The agent loop on its own
    ├── backend/                FastAPI, LangChain
    ├── data/                   The corpus it searches + its memory file
    ├── frontend/               Vite + React
    └── SETUP.md                Full setup, verification, troubleshooting
```
