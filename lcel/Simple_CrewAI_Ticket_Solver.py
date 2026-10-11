"""CrewAI ticket solver. Python 3.10–3.13.
Install: pip install crewai==1.15.27 python-dotenv==1.2.4
Live API calls require model access and quota.
Business functions are separate from the Flow wiring.
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

os.environ["CREWAI_TELEMETRY_DISABLED"] = "true"
os.environ["CREWAI_TRACING_ENABLED"] = "false"
from crewai import LLM
from crewai.flow.flow import Flow, start, listen
SAMPLE_TICKET = "My account is locked and I have an important meeting in 10 minutes."

async def ask(prompt: str) -> str:
    llm = LLM(model="openai/" + MODEL_NAME,
              base_url=os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1")
    return (await llm.acall(prompt)).strip()


async def clean_step(state):
    ticket = state['message'].strip()
    if not ticket:
        raise ValueError('Ticket cannot be empty.')
    state['ticket'] = ticket

async def analyse_ticket(state):
    ticket = state['ticket']
    summary = (await ask(f'Summarize this support ticket in one short sentence:\n{ticket}')).strip()
    category = (await ask(f'Return only one category: billing, technical, or account.\nTicket: {ticket}')).strip()
    urgency = (await ask(f'Return only one urgency: low, medium, or high.\nTicket: {ticket}')).strip()
    analysis: dict = {'summary': summary, 'category': category, 'urgency': urgency}
    state['analysis'] = analysis

async def add_decision(state):
    ticket = state['ticket']
    analysis = state['analysis']
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
    decision = (await ask(prompt)).strip()
    state['decision'] = decision

async def add_reply(state):
    ticket = state['ticket']
    decision = state['decision']
    prompt = f"""
    You are a customer-support assistant.

    Customer message:
    {ticket}

    Decision:
    {decision}

    Write a short and helpful reply to the customer.
    Do not mention prompts, AI, or internal system details.
    """
    reply = (await ask(prompt)).strip()
    state['reply'] = reply
    result = {'ticket': state['ticket'], 'analysis': state['analysis'], 'decision': state['decision'], 'reply': state['reply']}
    return result


# Only the workflow connections live here.
class TicketFlow(Flow):
    @start()
    async def clean(self):
        await clean_step(self.state)

    @listen(clean)
    async def analyse(self):
        await analyse_ticket(self.state)

    @listen(analyse)
    async def decide(self):
        await add_decision(self.state)

    @listen(decide)
    async def reply(self):
        return await add_reply(self.state)


async def solve_ticket(message: str) -> dict:
    result = await TicketFlow().kickoff_async(inputs={"message": message})

    print("\n========== TICKET RESULT (CrewAI) ==========")
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
