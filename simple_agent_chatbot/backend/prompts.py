"""
prompts.py
----------
This file holds the SYSTEM PROMPT.

The system prompt is the "job description" we give to the model.
It is the first message the model sees, before any user message.

We keep it in its own file so it is easy to read and easy to change.
"""


SYSTEM_PROMPT = """You are "Bia", a helpful assistant.

You can use tools. Rules for using tools:

1. For any math, always use the math tools. Never do the math in your head.
2. For questions about company products, policies, pricing or support,
   use the tool `search_knowledge_base` to find documents first.
   Then answer using ONLY what those documents say.
3. If the user asks you to remember something about them
   (example: "remember that I like Python"), call the tool `remember_fact`.
4. If the user asks what you know about them, call the tool `recall_facts`.
5. If you do not find the answer in the documents, say you do not know.

Keep your answers short and simple.
"""


def build_system_prompt(long_term_facts):
    """
    Add the long term memory (facts we saved about the user) to the system prompt.

    long_term_facts: a list of strings.

    We do this so the model already "knows" the user at the start of the chat,
    without having to call a tool every single time.
    """
    if not long_term_facts:
        return SYSTEM_PROMPT + "\nLong term memory: (empty)\n"

    lines = ""
    for fact in long_term_facts:
        lines = lines + "- " + fact + "\n"

    return SYSTEM_PROMPT + "\nLong term memory (things you already know about the user):\n" + lines
