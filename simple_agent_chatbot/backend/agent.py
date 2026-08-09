"""
agent.py
--------
THE AGENT.

What is an agent?

A normal LLM call is: question -> answer. One step. Finished.

An agent is a LOOP:

    1. Send [system prompt + history + question] to the model
    2. The model answers. Two possible answers:
         a) plain text   -> we are done, this is the final answer
         b) "call tool X with these arguments"
    3. If it asked for a tool, we RUN the python function,
       put the result back into the message list as a ToolMessage,
       and go back to step 1.
    4. Repeat until the model gives plain text.

We do NOT write this loop ourselves. `create_agent` from LangChain
already contains it. We only give it three things:

    the model  +  the tools  +  the system prompt
"""

import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

import long_term_memory
import short_term_memory
import trace
from prompts import build_system_prompt
from tools.registry import ALL_TOOLS


# Read the OPENAI_API_KEY from the .env file
load_dotenv()

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def build_agent():
    """
    Create the agent.

    We build it again on every message. Why?
    Because the system prompt contains the LONG TERM MEMORY, and the memory
    can change during the chat (the user can say "remember ..." any time).
    Rebuilding is cheap and much easier to understand.
    """

    # 1. The model. temperature=0 means: always give the most predictable answer.
    model = ChatOpenAI(model=MODEL_NAME, temperature=0)

    # 2. The system prompt, including everything we saved in long term memory.
    facts = long_term_memory.get_all_facts()
    system_prompt = build_system_prompt(facts)

    # 3. The agent = model + tools + system prompt
    agent = create_agent(model, ALL_TOOLS, system_prompt=system_prompt)

    # We also return the system prompt text, only so we can show it on screen.
    return agent, system_prompt


def run_agent(user_message, session_id):
    """
    Run one turn of the chat.

    Returns the final answer text, and the list of steps (the phases).
    """

    agent, system_prompt = build_agent()

    # SHORT TERM MEMORY: take the messages from earlier in this conversation
    history = short_term_memory.get_history(session_id)

    # Add the new question at the end
    messages_to_send = history + [HumanMessage(content=user_message)]

    # Run the agent loop. LangChain does the loop for us.
    # The result contains ALL messages, including the tool calls and tool results.
    result = agent.invoke({"messages": messages_to_send})

    all_messages = result["messages"]

    # The last message is always the final text answer of the model.
    final_answer = all_messages[-1].content

    # SHORT TERM MEMORY: save the conversation so the next question has context.
    # We save only the question and the answer, not every tool message,
    # to keep the history small and easy to read.
    new_history = history + [
        HumanMessage(content=user_message),
        all_messages[-1],
    ]
    short_term_memory.save_history(session_id, new_history)

    # `all_messages` starts with the old messages from short term memory,
    # because we sent them to the model again. For the screen we only want
    # what happened JUST NOW, so we cut the old part away.
    new_messages = all_messages[len(history):]

    # Build the phases and print them in the terminal
    steps = trace.build_steps(new_messages, system_prompt)
    trace.print_steps(steps)

    return final_answer, steps
