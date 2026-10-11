"""Microsoft ticket solver: clean -> analyse -> decide -> reply.

Install:
    pip install agent-framework-core==1.21.0 agent-framework-openai==1.16.0 python-dotenv==1.2.4
Use Python 3.11+. Set OPENAI_API_KEY in the environment or a local .env file.
The inherited model name must be available on your configured endpoint.
Running this file makes five live model calls for the sample ticket.

WorkflowContext is created by the framework, not by this file.
The workflow runtime supplies each executor a context connected to its state store.
TicketState below is a Python type declaration, not the state store constructor.
"""

import asyncio


MODEL_NAME = "gpt-4o-mini"  # Public OpenAI API model.

import os
import getpass
from dotenv import load_dotenv, find_dotenv


def read_openai_key():
    # In Colab, always use this notebook's enabled secret.
    try:
        from google.colab import userdata
    except ImportError:
        userdata = None
    if userdata is not None:
        try:
            key = userdata.get("OPENAI_API_KEY")
        except Exception:
            raise RuntimeError(
                "In Colab Secrets, add OPENAI_API_KEY and enable Notebook access, "
                "then rerun this cell."
            ) from None
        if not isinstance(key, str) or not key.strip():
            raise RuntimeError("The OPENAI_API_KEY Colab secret is empty.")
        return key.strip()

    # Local Python fallback; never overwrite an existing environment key.
    try:
        from dotenv import load_dotenv, find_dotenv
        load_dotenv(find_dotenv(usecwd=True), override=False)
    except ImportError:
        pass
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        from getpass import getpass
        key = getpass("Enter OPENAI_API_KEY (hidden): ").strip()
    if not key:
        raise ValueError("OPENAI_API_KEY cannot be empty.")
    return key


os.environ["OPENAI_API_KEY"] = read_openai_key()
print("OpenAI key loaded securely; authentication has not yet been tested.")

import os
from agent_framework import Agent, WorkflowBuilder, WorkflowContext, executor
from agent_framework.openai import OpenAIChatCompletionClient
from typing import Never

SAMPLE_TICKET = "My account is locked and I have an important meeting in 10 minutes."


client = OpenAIChatCompletionClient(
    model=MODEL_NAME,
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
)
agent = Agent(client=client, name="TicketSupport")
print(f"Agent configured for {MODEL_NAME}.")

from typing import TypedDict, Optional

class TicketState(TypedDict):
    ticket: str
    analysis: Optional[dict]
    decision: Optional[str]
    reply: Optional[str]

@executor(id="clean_step")
async def clean_step(message: str, ctx: WorkflowContext[str]) -> None:
    ticket = message.strip()
    if not ticket:
        raise ValueError("Ticket cannot be empty.")
    ctx.set_state("ticket", ticket)
    await ctx.send_message("continue")

@executor(id="analyse_ticket")
async def analyse_ticket(trigger: str, ctx: WorkflowContext[str]) -> None:
    ticket = ctx.get_state("ticket")

    summary = (await agent.run(
        f"Summarize this support ticket in one short sentence:\n{ticket}"
    )).text.strip()

    category = (await agent.run(
        f"Return only one category: billing, technical, or account.\nTicket: {ticket}"
    )).text.strip()

    urgency = (await agent.run(
        f"Return only one urgency: low, medium, or high.\nTicket: {ticket}"
    )).text.strip()

    analysis: dict = {
        "summary": summary,
        "category": category,
        "urgency": urgency,
    }
    ctx.set_state("analysis", analysis)
    await ctx.send_message("continue")

@executor(id="add_decision")
async def add_decision(trigger: str, ctx: WorkflowContext[str]) -> None:
    ticket = ctx.get_state("ticket")
    analysis = ctx.get_state("analysis")
    prompt = f"""
Review this ticket and the initial analysis:

Ticket:
{ticket}

Analysis:
{analysis}

Give the final decision:
1. Should this ticket be escalated to a human? (Yes/No)
2. Brief reason why.
"""

    decision = (await agent.run(prompt)).text.strip()

    ctx.set_state("decision", decision)
    await ctx.send_message("continue")

@executor(id="add_reply")
async def add_reply(trigger: str, ctx: WorkflowContext[Never, dict]) -> None:
    ticket = ctx.get_state("ticket")
    decision = ctx.get_state("decision")
    prompt = f"""
You are a customer-support assistant.

Customer message:
{ticket}

Decision:
{decision}

Write a short and helpful reply to the customer.
Do not mention prompts, AI, or internal system details.
"""

    reply = (await agent.run(prompt)).text.strip()

    ctx.set_state("reply", reply)
    result: TicketState = {
        "ticket": ctx.get_state("ticket"),
        "analysis": ctx.get_state("analysis"),
        "decision": ctx.get_state("decision"),
        "reply": ctx.get_state("reply"),
    }
    await ctx.yield_output(result)

def create_workflow():
    return (
        WorkflowBuilder(start_executor=clean_step, output_from=[add_reply])
        .add_edge(clean_step, analyse_ticket)
        .add_edge(analyse_ticket, add_decision)
        .add_edge(add_decision, add_reply)
        .build()
    )

async def solve_ticket(message: str) -> TicketState:
    workflow = create_workflow()
    run_result = await workflow.run(message)
    outputs = run_result.get_outputs()
    if len(outputs) != 1:
        raise RuntimeError(f"Expected one final result; got {len(outputs)}.")
    result = outputs[0]

    print("\n========== TICKET RESULT (Microsoft Agent Framework) ==========")
    print("Message  :", result["ticket"])
    print("\nAnalysis :")
    for key, val in result["analysis"].items():
        print(f"  - {key}: {val}")
    print("\nDecision :\n", result["decision"])
    print("\nReply to customer:\n", result["reply"])
    print("===============================================================")
    return result

if __name__ == "__main__":
    asyncio.run(solve_ticket(SAMPLE_TICKET))
