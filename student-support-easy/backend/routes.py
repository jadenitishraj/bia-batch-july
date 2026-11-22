"""These are the URLs that React calls."""
import json
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from backend import database, ai, live

router = APIRouter()


@router.get("/api/state")
async def state():
    return live.snapshot()


@router.websocket("/ws")
async def live_updates(browser: WebSocket):
    origin = browser.headers.get("origin")
    if origin and origin not in ["http://127.0.0.1:8002", "http://localhost:8002", "http://127.0.0.1:5174", "http://localhost:5174"]:
        await browser.close(code=1008)
        return
    await browser.accept()
    live.browsers.add(browser)
    await browser.send_json(live.snapshot())
    try:
        while True:
            await browser.receive_text()
    except WebSocketDisconnect:
        live.browsers.discard(browser)


@router.post("/api/chat")
async def chat(body: dict):
    async def chunks():
        try:
            async for text in ai.reply(body.get("message", ""), body.get("history", [])):
                yield "data: " + json.dumps({"text": text}) + "\n\n"
        except Exception:
            yield "data: " + json.dumps({"text": "Gemini could not finish. Check its API key or quota."}) + "\n\n"
    return StreamingResponse(chunks(), media_type="text/event-stream")


@router.post("/api/demo")
async def sample():
    email = {"id": "demo-" + str(time.time_ns()), "subject": "Demo: BIA FastAPI help", "received_at": time.time()}
    database.remember(email)
    database.save_status(email["id"], "done (demo)", "Tomorrow, 04:00 PM IST — sample only")
    database.add_notice(email["id"], "Demo: a BIA request and sample meeting were saved. No Google write was made.")
    await live.broadcast()
    return {"message": "Sample added. No real email or meeting was created."}
