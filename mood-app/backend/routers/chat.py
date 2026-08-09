# The chat routes.
# /chat gives the agent's reply plus a trace of how it got there.
# /explain turns that trace into a plain-words explanation for students.

from fastapi import APIRouter

from agent import ask_agent
from explainer import explain_trace
from schemas import ChatIn, ExplainIn

router = APIRouter(tags=["chat"])


@router.post("/chat")
async def chat(data: ChatIn):
    reply, trace = await ask_agent(data.message, data.history)
    return {"reply": reply, "trace": trace}


@router.post("/explain")
async def explain(data: ExplainIn):
    return {"explanation": await explain_trace(data.trace)}
