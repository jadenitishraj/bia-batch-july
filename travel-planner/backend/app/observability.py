"""Optional LangSmith proof using a fixed synthetic trip, never uploaded documents."""
import json
import os
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langsmith import Client, traceable, tracing_context
from starlette.concurrency import run_in_threadpool

router = APIRouter(prefix='/api/observability')
DEMO_REQUEST = (
    'Find only flights from Mumbai to Singapore for one adult, budget INR 25000. '
    'Avoid red-eye flights. Use the sample travel data. No hotels or activities. '
    'Do not use uploaded documents. Keep the answer brief.'
)


def demo_client():
    key = os.getenv('TRAVEL_PLANNER_LANGSMITH_API_KEY')
    if not key:
        raise HTTPException(503, 'Configure TRAVEL_PLANNER_LANGSMITH_API_KEY privately to run the trace demo.')
    return Client(
        api_key=key, api_url='https://api.smith.langchain.com', timeout_ms=10000,
        hide_inputs=True, hide_outputs=True, hide_metadata=True,
    )


@traceable(name='Travel Planner classroom workflow', run_type='chain')
async def synthetic_workflow():
    """Stream the real graph; exceptions escape so LangSmith marks failed runs correctly."""
    from .graph import travel_planner
    yield {'type': 'started'}
    async for update in travel_planner.astream(
        {'request': DEMO_REQUEST},
        config={'run_name': 'Travel Planner graph', 'recursion_limit': 50},
        stream_mode='updates',
    ):
        for node, state in update.items():
            yield {'type': 'step', 'node': node, 'state': state}
            if 'final_plan' in state:
                yield {'type': 'result', 'answer': state['final_plan']}
    yield {'type': 'done'}


async def demo_events(client, run_id, project):
    try:
        with tracing_context(enabled=True, client=client, project_name=project,
                             tags=['synthetic-demo', 'bia-july-travel-planner']):
            async for event in synthetic_workflow(langsmith_extra={'run_id': run_id}):
                yield json.dumps(event) + '\n'
    except Exception:  # noqa: BLE001 - never expose provider details in the demo stream
        yield json.dumps({'type': 'error', 'message': 'Synthetic planning failed. Inspect the trace for the failed step.'}) + '\n'
    finally:
        await run_in_threadpool(client.flush, timeout=10)
    yield json.dumps({'type': 'trace', 'run_id': str(run_id), 'project': project}) + '\n'


@router.post('/demo')
async def trace_demo():
    """Explicit local demo endpoint. It accepts no caller-supplied request or excerpts."""
    client = demo_client()
    run_id = uuid4()
    project = os.getenv('TRAVEL_PLANNER_LANGSMITH_PROJECT', 'bia-july-travel-planner-demo')
    return StreamingResponse(demo_events(client, run_id, project),
                             media_type='application/x-ndjson',
                             headers={'Cache-Control': 'no-store', 'X-Trace-Id': str(run_id)})
