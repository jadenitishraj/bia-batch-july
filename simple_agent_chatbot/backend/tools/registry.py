"""
registry.py
-----------
THE TOOL REGISTRY.

This is the ONE place where we collect every tool of the app.

Why do we need it?
The agent needs a single list of tools. Instead of the agent importing from
5 different files, every tool file is imported here, and the agent only
imports ALL_TOOLS from this file.

To add a new tool:
  1. write the function with @tool in one of the files below
  2. add its name to the ALL_TOOLS list here
That is all. The agent will be able to use it immediately.
"""

from tools import data_tools, math_tools, memory_tools, text_tools


ALL_TOOLS = [
    # --- math tools ---
    math_tools.add,
    math_tools.subtract,
    math_tools.multiply,
    math_tools.divide,
    math_tools.percent_of,

    # --- data tools (our JSON corpus, like a small web search) ---
    data_tools.search_knowledge_base,
    data_tools.get_document,
    data_tools.list_topics,

    # --- long term memory tools ---
    memory_tools.remember_fact,
    memory_tools.recall_facts,
    memory_tools.forget_everything,

    # --- small helper tools ---
    text_tools.get_current_time,
    text_tools.count_words,
    text_tools.to_uppercase,
    text_tools.reverse_text,
]


def print_tools():
    """Print the name and description of every tool. Useful to explain the registry."""
    print("\nTOOL REGISTRY -", len(ALL_TOOLS), "tools available\n")

    for t in ALL_TOOLS:
        print("  *", t.name)
        print("     ", t.description.replace("\n", " ")[:100])

    print("")
