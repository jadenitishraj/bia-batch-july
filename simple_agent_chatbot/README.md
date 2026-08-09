# Simple Agent Chatbot

A small teaching project that shows how a **tool calling AI agent** works, using
**LangChain + OpenAI + FastAPI + React**.

Everything is written in plain, simple Python. No clever tricks.

---

**Setting it up for the first time?** Follow [SETUP.md](SETUP.md) — it has the full sequence,
verification steps and a troubleshooting table.

**Slides:** the decks are shared across the course and live one level up. Open
[../presentations/simple-agent-architecture.html](../presentations/simple-agent-architecture.html)
in a browser — 15 slides covering every concept below, plus a section on choosing between
LangChain, LangGraph, CrewAI and AutoGen.

---

## 1. What you will learn

| Idea | Where to look |
|---|---|
| What a system prompt is | `backend/prompts.py` |
| What a tool is | `backend/tools/math_tools.py` |
| How tools are collected in one place | `backend/tools/registry.py` |
| What an agent is (the loop) | `backend/agent.py` |
| How tool call messages are passed | `backend/trace.py` |
| Short term memory (this conversation) | `backend/short_term_memory.py` |
| Long term memory (a JSON file) | `backend/long_term_memory.py` |
| How an API talks to an agent | `backend/main.py` |
| How a UI talks to the API | `frontend/src/App.jsx` |

---

## 2. The folders

```
simple_agent_chatbot/
├── backend/
│   ├── main.py                 FastAPI - the API. React talks to this.
│   ├── agent.py                The agent = model + tools + system prompt
│   ├── prompts.py              The system prompt
│   ├── trace.py                Prints every phase of an agent run
│   ├── short_term_memory.py    The current chat, kept in RAM
│   ├── long_term_memory.py     Facts saved forever in a JSON file
│   ├── test_agent.py           Run the agent in the terminal, no UI needed
│   └── tools/
│       ├── registry.py         THE TOOL REGISTRY - all tools in one list
│       ├── math_tools.py       add, subtract, multiply, divide, percent_of
│       ├── data_tools.py       search our JSON corpus (like a web search)
│       ├── memory_tools.py     remember_fact, recall_facts, forget_everything
│       └── text_tools.py       time, word count, uppercase, reverse
├── data/
│   ├── corpus.json             Our documents. The bot answers from these.
│   └── long_term_memory.json   The memory file. It grows as you chat.
└── frontend/
    └── src/App.jsx             The React chat screen
```

---

## 3. How to run it

### Step 1 - the API key

Copy `.env.example` to `.env` and put your OpenAI key inside:

```bash
cp .env.example .env
```

```
OPENAI_API_KEY=sk-your-real-key
OPENAI_MODEL=gpt-4o-mini
```

### Step 2 - install python packages

LangChain needs **Python 3.10 or newer**. Check your version first:

```bash
python3 --version
```

If it says 3.9 or older, install a newer python (for example `brew install python@3.11`)
and use that command instead of `python3` in the next line.

```bash
python3 -m venv .venv && ./.venv/bin/pip install -r backend/requirements.txt
```

The `.venv` folder is **not** in the repository — everyone creates their own, because a virtual
environment only works on the machine that built it. So do not skip this step.

### Step 3 - try the agent in the terminal first (best for teaching)

```bash
cd backend && ../.venv/bin/python test_agent.py
```

No API, no React. You type a question and you see every phase printed.

### Step 4 - start the API

```bash
cd backend && ../.venv/bin/uvicorn main:app --reload --port 8001
```

Open http://localhost:8001/docs to try the API without React.

### Step 5 - start React (in a second terminal)

```bash
cd frontend && npm install && npm run dev
```

Open http://localhost:5173

---

## 4. The most important idea: an agent is a growing list of messages

There are 4 kinds of message:

| Message | Meaning |
|---|---|
| `SystemMessage` | The rules. Our system prompt. |
| `HumanMessage` | What the user typed. |
| `AIMessage` | What the model said. If it wants a tool, the text is empty and it has `tool_calls` instead. |
| `ToolMessage` | What our python function returned. This goes **back to the model**. |

So "what is 12 times 8?" really becomes:

```
HumanMessage  "what is 12 times 8?"
AIMessage     tool_calls = [ multiply(a=12, b=8) ]     <- model ASKS, it does not run anything
ToolMessage   "96.0"                                    <- our python function ran and answered
AIMessage     "12 times 8 is 96."                       <- final answer, no tool_calls
```

**The model never runs your code.** It only says which function it wants and with
which arguments. LangChain runs the python function and puts the answer back into
the list as a `ToolMessage`. Then the model reads it and continues.

That back-and-forth is the whole "agent loop". `create_agent` in `agent.py`
contains that loop, so we do not write it ourselves.

You can see all of this in the right panel of the React screen, and printed in
the terminal where uvicorn is running.

---

## 5. The two memories

**Short term memory** (`short_term_memory.py`) is a python dictionary in RAM.
It holds the current conversation, so the bot understands follow-up questions
like *"and what about the Business plan?"*. It is **lost when you restart the server**.
We keep only the last 10 messages so the prompt does not become huge.

**Long term memory** (`long_term_memory.py`) is the file `data/long_term_memory.json`.
It **survives a restart**. It is filled by the agent itself: when the user says
*"remember that I live in Pune"*, the model calls the tool `remember_fact`, and our
python code writes into the JSON file. Before every question, everything in that
file is put into the system prompt, so the bot already knows the user.

Open `data/long_term_memory.json` while you chat — you will see it grow.

### An important detail: the whole conversation is sent every single time

The model has **no memory of its own**. On every question we send it the system
prompt plus all the old messages again. That is the only reason it can answer a
follow-up like *"and what about cancelling?"*.

The phases panel shows only what happened **just now**, otherwise it would repeat
the whole conversation on every message. Instead there is one grey line at the
top: *"Short term memory: N older messages were also sent to the model"*.

To see those older messages, open:

    http://localhost:8001/memory/short-term

`agent.py` does the cut with `all_messages[len(history):]` — everything before
that point is the replayed history, everything after it is new.

---

## 6. Things to try in the chat

| What you type | What you should see |
|---|---|
| `what is 25 times 4 plus 10?` | two tool calls, one after the other |
| `what is 15 percent of 200?` | the `percent_of` tool |
| `what is the refund policy?` | `search_knowledge_base` reads `corpus.json` |
| `and what about cancelling?` | short term memory understood the follow-up |
| `remember that I live in Pune` | `remember_fact` writes into the JSON file |
| `what do you remember about me?` | `recall_facts` |
| `who is the president of France?` | no tool, and it should say it does not know |

---

## 7. How to add your own tool (3 minutes)

1. Open `backend/tools/math_tools.py` (or make a new file in `tools/`).
2. Write a normal python function with `@tool` on top:

```python
@tool
def square(number: float) -> float:
    """Multiply a number by itself. Use this when the user asks for a square."""
    return number * number
```

3. Add it to the list in `backend/tools/registry.py`:

```python
math_tools.square,
```

Done. Restart the server and the agent can use it.

The **docstring is the most important part** — that text is the tool description,
and the model reads it to decide when to use your tool. A bad docstring means the
model will call the wrong tool.
