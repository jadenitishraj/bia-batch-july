"""Ticket solver using one sequential Crew, without Flow.
Python 3.10–3.13. Install: pip install crewai==1.15.27 python-dotenv==1.2.4
"""
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


os.environ["CREWAI_TELEMETRY_DISABLED"] = "true"
os.environ["CREWAI_TRACING_ENABLED"] = "false"
import asyncio
import os
from crewai import Agent, Task, Crew, Process, LLM
from pydantic import BaseModel

MODEL_NAME = "gpt-4o-mini"
SAMPLE_TICKET = "My account is locked and I have an important meeting in 10 minutes."

class TicketAnalysis(BaseModel):
    summary: str
    category: str
    urgency: str

def create_crew(ticket: str) -> Crew:
    llm = LLM(model="openai/" + MODEL_NAME,
              base_url=os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1")

    analyst = Agent(
        role="Ticket analyst", goal="Summarize and classify support tickets.",
        backstory="You triage customer support requests.",
        llm=llm, allow_delegation=False, max_iter=8,
    )
    decision_maker = Agent(
        role="Escalation reviewer", goal="Decide whether human help is needed.",
        backstory="You review ticket urgency and support needs.",
        llm=llm, allow_delegation=False, max_iter=8,
    )
    reply_writer = Agent(
        role="Support reply writer", goal="Write short, helpful customer replies.",
        backstory="You explain the next support steps clearly.",
        llm=llm, allow_delegation=False, max_iter=8,
    )

    analyse = Task(
        description=f"Summarize this ticket in one sentence, choose category "
                    f"billing, technical or account, and urgency low, medium or high.\nTicket: {ticket}",
        expected_output="JSON with summary, category and urgency.",
        output_json=TicketAnalysis,
        agent=analyst,
    )
    decide = Task(
        description=f"Review the ticket and analysis. Should it be escalated "
                    f"to a human? Answer Yes/No with a brief reason.\nTicket: {ticket}",
        expected_output="An escalation decision and brief reason.",
        agent=decision_maker,
        context=[analyse],
    )
    reply = Task(
        description=f"Write a short helpful reply using the analysis and decision. "
                    f"Do not mention prompts, AI or internal system details. "
                    f"Do not claim any escalation action has already happened.\nTicket: {ticket}",
        expected_output="Only the customer-facing reply.",
        agent=reply_writer,
        context=[analyse, decide],
    )

    # The whole workflow is here: tasks run in this order.
    return Crew(
        agents=[analyst, decision_maker, reply_writer],
        tasks=[analyse, decide, reply],
        process=Process.sequential,
        memory=False, cache=False, verbose=False, tracing=False,
    )


async def solve_ticket(message: str) -> dict:
    ticket = message.strip()
    if not ticket:
        raise ValueError("Ticket cannot be empty.")

    crew = create_crew(ticket)
    output = await crew.kickoff_async()
    analysis_output, decision_output, reply_output = output.tasks_output
    if analysis_output.json_dict is None:
        raise ValueError("The analysis task did not return valid structured data.")
    return {
        "ticket": ticket,
        "analysis": analysis_output.json_dict,
        "decision": decision_output.raw.strip(),
        "reply": reply_output.raw.strip(),
    }

if __name__ == "__main__":
    os.environ["OPENAI_API_KEY"] = read_openai_key()
    print(asyncio.run(solve_ticket(SAMPLE_TICKET)))
