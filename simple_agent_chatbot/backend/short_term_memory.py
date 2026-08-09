"""
short_term_memory.py
--------------------
SHORT TERM MEMORY = the current conversation.

It is just a python dictionary kept in RAM:

    {
      "session-1": [HumanMessage("hi"), AIMessage("hello")],
      "session-2": [...]
    }

When you restart the server, this is GONE. That is the difference
between short term memory and long term memory.

We also keep only the last few messages, so the prompt does not become huge.
"""


# session_id  ->  list of langchain messages
CHAT_HISTORY = {}

# How many messages we keep per session (10 = about 5 questions and 5 answers)
MAX_MESSAGES = 10


def get_history(session_id):
    """Return the message list for this session. Create an empty one if new."""
    if session_id not in CHAT_HISTORY:
        CHAT_HISTORY[session_id] = []

    return CHAT_HISTORY[session_id]


def save_history(session_id, messages):
    """Save the message list, keeping only the last MAX_MESSAGES messages."""
    CHAT_HISTORY[session_id] = messages[-MAX_MESSAGES:]


def clear_history(session_id):
    """Forget the current conversation for this session."""
    CHAT_HISTORY[session_id] = []


def as_json(session_id):
    """
    Turn the saved messages into plain dictionaries, so they can be sent
    to React as JSON and shown on the screen.

    A LangChain message object cannot travel over the network as it is,
    so we copy the two parts we care about: what kind it is, and its text.
    """
    messages = []

    for m in get_history(session_id):
        messages.append({
            "type": m.__class__.__name__,
            "content": m.content,
        })

    return messages
