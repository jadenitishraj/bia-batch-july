# The chatbot brain, built with the OpenAI Agents SDK.
# We give the agent a personality (instructions) and the list of tools it may use.

import os

from agents import Agent, Runner

from agent_trace import build_trace
from tools import ALL_TOOLS

INSTRUCTIONS = """
You are the assistant inside a personal notes app.

You can read and change the user's notes, categories, tags and moods by using your tools.
Always use a tool to get real data. Never guess or invent notes.

Helpful habits:
- Before creating a note with a category, mood or tag that may not exist, list them first
  and create the missing one, then create the note.
- To edit or delete a note, first use list_notes to find its id.
- For questions like "how many times was I happy", use count_notes_by_mood, and if the user
  wants to see them, also use list_notes with that mood.

Reply in a short, warm and friendly way. Use simple language and a little formatting.
"""

notes_agent = Agent(
    name="Notes Assistant",
    instructions=INSTRUCTIONS,
    model="gpt-4.1-mini",
    tools=ALL_TOOLS,
)


async def ask_agent(message: str, history: list[dict]) -> tuple[str, dict | None]:
    """Send one message (plus the earlier chat) to the agent.

    Returns the reply and a trace: a record of everything that happened, which the
    "eye" button in the app shows to students.
    """
    if not os.getenv("OPENAI_API_KEY"):
        return "Please add your OPENAI_API_KEY to backend/.env and restart the server.", None

    result = await Runner.run(notes_agent, history + [{"role": "user", "content": message}])
    return result.final_output, build_trace(notes_agent, message, history, result)
