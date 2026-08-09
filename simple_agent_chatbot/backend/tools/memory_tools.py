"""
memory_tools.py
---------------
Tools that let the AGENT write into LONG TERM MEMORY.

This is the interesting part:
the model itself decides when to save something, by calling `remember_fact`.

When the user says "remember that I work in Bangalore", the model will call:

    remember_fact(fact="The user works in Bangalore")

and our python code writes it into data/long_term_memory.json.
"""

from langchain_core.tools import tool

import long_term_memory


@tool
def remember_fact(fact: str) -> str:
    """Save one fact about the user into long term memory, so it is remembered forever.
    Use this whenever the user says 'remember ...' or tells you something personal
    that will be useful later, like their name, their city, or what they like.
    Write the fact as a short full sentence, for example 'The user lives in Pune'."""

    long_term_memory.add_fact(fact)
    return "Saved to long term memory: " + fact


@tool
def recall_facts() -> str:
    """Read everything currently saved in long term memory about the user.
    Use this when the user asks what you know or remember about them."""

    facts = long_term_memory.get_all_facts()

    if len(facts) == 0:
        return "Long term memory is empty."

    output = "I remember these facts:\n"
    for fact in facts:
        output = output + "- " + fact + "\n"

    return output


@tool
def forget_everything() -> str:
    """Delete everything from long term memory.
    Only use this when the user clearly asks to forget everything."""

    long_term_memory.clear_facts()
    return "Long term memory is now empty."
