"""
main.py
-------
THE API (FastAPI).

This is the door of our backend. React talks to this file, and this file
talks to the agent.

The full journey of one message:

    React  --POST /chat-->  main.py  -->  agent.py  -->  OpenAI model
                                             |               |
                                             |          "call add(2,3)"
                                             v
                                        tools/math_tools.py  -> 5
                                             |
                                             v
                                        model writes final answer
    React  <--- answer + steps ---  main.py

Run it with:
    uvicorn main:app --reload --port 8001

Then open http://localhost:8001/docs to try the API without React.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import agent
import long_term_memory
import short_term_memory
from tools.registry import ALL_TOOLS


app = FastAPI(title="Simple Agent Chatbot")

# CORS = permission for the React app (port 5173) to call this API (port 8000).
# Without this the browser blocks the request.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """This describes the JSON that React must send us."""
    message: str
    session_id: str = "default"


@app.get("/")
def home():
    """A simple check that the server is alive."""
    return {"status": "ok", "tools": len(ALL_TOOLS)}


@app.get("/tools")
def get_tools():
    """Show every tool in the registry, with its description."""
    tool_list = []

    for t in ALL_TOOLS:
        tool_list.append({"name": t.name, "description": t.description})

    return {"count": len(tool_list), "tools": tool_list}


@app.post("/chat")
def chat(request: ChatRequest):
    """
    The main endpoint. React calls this every time the user sends a message.
    """

    print("\n>>> API HIT: POST /chat")
    print(">>> session:", request.session_id)
    print(">>> message:", request.message)

    # Give the work to the agent
    answer, steps = agent.run_agent(request.message, request.session_id)

    print(">>> API RETURNING the answer to React\n")

    return {
        "answer": answer,
        "steps": steps,
        # the WHOLE conversation we are keeping in RAM, after this turn
        "short_term_memory": short_term_memory.as_json(request.session_id),
        "short_term_memory_size": len(short_term_memory.get_history(request.session_id)),
        "long_term_memory": long_term_memory.get_all_facts(),
    }


@app.get("/memory/long-term")
def get_long_term_memory():
    """Read the JSON file with the facts we saved forever."""
    return long_term_memory.load_memory()


@app.get("/memory/short-term")
def get_short_term_memory(session_id: str = "default"):
    """Read the current conversation kept in RAM."""
    return {
        "session_id": session_id,
        "messages": short_term_memory.as_json(session_id),
    }


@app.post("/memory/short-term/clear")
def clear_short_term_memory(session_id: str = "default"):
    """Forget the current conversation, but keep the long term facts."""
    short_term_memory.clear_history(session_id)
    return {"status": "short term memory cleared"}
