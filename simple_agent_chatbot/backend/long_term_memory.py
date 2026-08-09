"""
long_term_memory.py
-------------------
LONG TERM MEMORY = things we want to keep FOREVER.

It survives even after you stop the server, because we save it in a JSON file:
    data/long_term_memory.json

The JSON file looks like this:

{
  "facts": [
    {"fact": "The user likes Python", "saved_at": "2026-08-08 10:30:00"}
  ]
}

Every time we add a fact, we write the whole file again. Simple and easy to read.
"""

import json
import os
import threading
from datetime import datetime


# The model can ask for two tools AT THE SAME TIME
# (example: "remember I live in Pune and I like Python" -> 2 calls to remember_fact).
# This lock makes sure only one of them writes the file at a time,
# otherwise one fact would overwrite the other and get lost.
LOCK = threading.Lock()


# Find the path of data/long_term_memory.json
# __file__ is this file. We go one folder up (backend -> project) then into data/
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_FOLDER = os.path.dirname(HERE)
MEMORY_FILE = os.path.join(PROJECT_FOLDER, "data", "long_term_memory.json")


def load_memory():
    """Read the JSON file and return the python dictionary."""
    if not os.path.exists(MEMORY_FILE):
        return {"facts": []}

    with open(MEMORY_FILE, "r") as f:
        return json.load(f)


def save_memory(memory):
    """Write the python dictionary back into the JSON file."""
    # We write into a temporary file first, then rename it.
    # Renaming happens in one single step, so nobody can ever read
    # a half written file.
    temp_file = MEMORY_FILE + ".tmp"

    with open(temp_file, "w") as f:
        json.dump(memory, f, indent=2)

    os.replace(temp_file, MEMORY_FILE)


def add_fact(fact):
    """Add one new fact and save the file."""
    with LOCK:
        memory = load_memory()

        new_item = {
            "fact": fact,
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        memory["facts"].append(new_item)

        save_memory(memory)

    return new_item


def get_all_facts():
    """Return the facts as a simple list of strings."""
    memory = load_memory()

    facts = []
    for item in memory["facts"]:
        facts.append(item["fact"])

    return facts


def clear_facts():
    """Delete everything from long term memory."""
    with LOCK:
        save_memory({"facts": []})
