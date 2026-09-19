from .registry import TOOL_REGISTRY
from langchain.agents import create_agent

MODEL = "openai:gpt-4o-mini"     # small, fast and cheap. Change to gpt-4o for better writing.


def ask(agent, question: str) -> str:
    """Send a question to an agent and get its final answer back as plain text."""
    reply = agent.invoke({"messages": [{"role": "user", "content": question}]})
    return reply["messages"][-1].content


# ---------- The manager. No tools. It thinks and writes. ----------
manager_agent = create_agent(
    model=MODEL,
    tools=[],
    system_prompt=(
        "You are the manager of a travel planning team. "
        "You never search for travel data yourself. "
        "You read the request, decide who should work, and write the final plan. "
        "Be short and clear. Never invent a flight, hotel or place that a worker did not give you."
    ),
)

# ---------- Flight agent ----------
flight_agent = create_agent(
    model=MODEL,
    tools=TOOL_REGISTRY["flight_agent"],
    system_prompt=(
        "You are the flight specialist. Use your tools to find real options. "
        "Never suggest a flight that did not come from a tool. "
        "Answer in exactly this shape:\n"
        "TOP 3 OPTIONS: a numbered list with airline, flight id, times and price\n"
        "RECOMMENDED: one option and one line saying why\n"
        "TRADE-OFFS: what the traveller gives up by taking it\n"
        "ASSUMPTIONS: anything you had to guess"
    ),
)

# ---------- Hotel agent ----------
hotel_agent = create_agent(
    model=MODEL,
    tools=TOOL_REGISTRY["hotel_agent"],
    system_prompt=(
        "You are the hotel specialist. Use your tools to find real options. "
        "Never suggest a hotel that did not come from a tool. "
        "Always check the total cost for the whole stay, not only the price per night. "
        "Answer in exactly this shape:\n"
        "TOP 3 OPTIONS: a numbered list with name, area, rating, price per night, total for the stay\n"
        "RECOMMENDED: one option and one line saying why\n"
        "TRADE-OFFS: what the traveller gives up by taking it\n"
        "ASSUMPTIONS: anything you had to guess"
    ),
)

# ---------- Activity agent ----------
activity_agent = create_agent(
    model=MODEL,
    tools=TOOL_REGISTRY["activity_agent"],
    system_prompt=(
        "You are the activities specialist. Use your tools to find real places. "
        "Never suggest a place that did not come from a tool. "
        "Do not overload a day. Two or three activities plus one meal is enough. "
        "Answer in exactly this shape:\n"
        "DAY BY DAY: for each day, morning, afternoon, evening and where to eat\n"
        "WEATHER NOTE: one line\n"
        "ASSUMPTIONS: anything you had to guess"
    ),
)

# ---------- Critic agent ----------
critic_agent = create_agent(
    model=MODEL,
    tools=TOOL_REGISTRY["critic_agent"],
    system_prompt=(
        "You are a strict reviewer of travel plans. You do not rewrite the plan. "
        "You list problems only. "
        "Check four things: budget respected, days not overloaded, the traveller's stated "
        "interests actually appear, and guesses are stated honestly. "
        "Answer as a numbered list of specific fixes. "
        "Never write vague comments like 'make it better'. "
        "If the plan is fine, say NO ISSUES FOUND."
    ),
)

print("5 agents ready: manager, flight, hotel, activity, critic.")