"""
test_agent.py
-------------
Run the agent from the terminal, WITHOUT React and WITHOUT FastAPI.

This is the best file to start with when you are teaching, because
nothing is hidden: you type a question, and you see every phase printed.

Run it like this (from the backend folder):

    python test_agent.py
"""

import agent
from tools.registry import print_tools


# First show every tool the agent is allowed to use
print_tools()

print("Type your question. Type 'quit' to stop.\n")

while True:
    question = input("You: ")

    if question.lower() in ["quit", "exit"]:
        break

    answer, steps = agent.run_agent(question, session_id="terminal")

    print("Bia:", answer, "\n")
