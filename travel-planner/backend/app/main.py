"""HTTP interface for the notebook's unchanged travel planning graph."""
import json
import re
from typing import Annotated
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from langsmith import tracing_context
from pydantic import BaseModel, Field, StringConstraints
from starlette.concurrency import run_in_threadpool

load_dotenv(Path(__file__).resolve().parents[2] / '.env')
from .system_observability import RequestObserver, lifespan
from .event_log import log_event
app = FastAPI(title='Travel Planner', lifespan=lifespan)
app.add_middleware(RequestObserver)
from .documents import router as documents_router
from .document_answers import classify_request, answer_documents
from .models import is_configured
from .observability import router as observability_router
app.include_router(documents_router)
app.include_router(observability_router)


class TripRequest(BaseModel):
    request: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]


@app.get('/api/health')
def health():
    return {'status': 'ok', 'configured': is_configured()}


@app.post('/api/plan')
async def plan(payload: TripRequest):
    greeting = re.sub(r'[^a-z ]', '', payload.request.lower()).strip()
    if greeting in {'hi', 'hello', 'hey', 'hi there', 'hello there', 'good morning', 'good afternoon', 'good evening', 'thanks', 'thank you'}:
        answer = "Hi! I can help plan your trip or answer questions about your uploaded documents. Where would you like to start?"
        events = [{'type': 'started'}, {'type': 'result', 'answer': answer}, {'type': 'done'}]
        return StreamingResponse(iter(json.dumps(event) + '\n' for event in events), media_type='application/x-ndjson')
    if not is_configured():

        raise HTTPException(503, 'Configure the selected AI provider and its API key in the project .env, then restart the backend.')
    from .graph import travel_planner

    def event(data):
        return json.dumps(data) + '\n'

    async def events():
        yield event({'type': 'started'})
        try:
            intent = await run_in_threadpool(classify_request, payload.request)
            log_event('request.routing', travel=intent.travel, documents=intent.documents)
            final_plan = ''
            if not intent.travel and not intent.documents:
                yield event({'type': 'result', 'answer': 'I can help with travel plans and your uploaded documents. Tell me a destination or ask a document question.'})
            if intent.travel:
                async for update in travel_planner.astream(
                    {'request': payload.request.strip()},
                    config={'recursion_limit': 50}, stream_mode='updates',
                ):
                    for node, state in update.items():
                        yield event({'type': 'step', 'node': node, 'state': state})
                        if 'final_plan' in state:
                            final_plan = state['final_plan']
                            yield event({'type': 'result', 'answer': final_plan})
            if intent.documents:
                yield event({'type': 'status', 'message': 'Searching your documents…'})
                try:
                    document = await run_in_threadpool(answer_documents, payload.request)
                    yield event({'type': 'step', 'node': 'documents',
                                 'state': {'retrieved_excerpts': document['context']}})
                    final_plan += ('\n\n---\n\n' if final_plan else '') + '## From your documents\n\n' + document['answer']
                    yield event({'type': 'result', 'answer': final_plan})
                except Exception:
                    yield event({'type': 'error', 'message': 'Document retrieval failed in the original RAG pipeline. Any trip answer above is still available. The RAG code has not been changed; check the backend output.'})
            yield event({'type': 'done'})
        except Exception as error:
            # Never return provider payloads, credentials, or tracebacks to the browser.
            name = type(error).__name__
            messages = {
                'AuthenticationError': 'The API key was rejected. Update the project .env and restart the backend.',
                'RateLimitError': 'The AI provider rate limit or quota was reached. Check your API billing and try again.',
                'APIConnectionError': 'Could not reach the AI provider. Check your connection and try again.',
                'GoogleAuthenticationError': 'The Gemini key was rejected. Check the project .env.',
                'GooglePermissionDeniedError': 'Gemini access was denied. Check the key and model access.',
                'GoogleRateLimitError': 'Gemini quota or rate limit reached. Please try again later.',
                'GoogleAPIError': 'Gemini is temporarily unavailable. Please try again later.',
            }
            yield event({'type': 'error', 'message': messages.get(name, 'Planning could not finish. Please try again with a more specific trip request.')})

    async def stream():
        with tracing_context(enabled=False):
            async for line in events():
                yield line

    return StreamingResponse(stream(), media_type='application/x-ndjson', headers={'Cache-Control': 'no-cache'})
