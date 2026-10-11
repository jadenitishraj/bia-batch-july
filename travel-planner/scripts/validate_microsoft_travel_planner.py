"""Developer-only transport fixtures and validation for the live teaching notebook.
Run with Python 3.10+ and installed notebook dependencies plus nbformat/httpx2.
No real credentials or network/model calls are used. Narratives only exercise the fixed sample.
"""
import os, json, asyncio
MODEL = "gpt-4o-mini"
from openai import AsyncOpenAI
import httpx2
OFFLINE_WORKERS = 'flight_agent, hotel_agent, activity_agent'
OFFLINE_CRITIQUE = '1. Clarify that flight prices are one-way per person and hotel totals assume three nights.'
OFFLINE_TRACE = []
OFFLINE_HTTP_CLIENTS = []

async def offline_response(request):
    payload = json.loads(request.content)
    messages = payload['messages']
    prompt = next((m['content'] for m in messages if m['role'] == 'user'))
    tool_messages = [m for m in messages if m['role'] == 'tool']
    schemas = payload.get('tools', [])
    names = [t['function']['name'] for t in schemas]
    OFFLINE_TRACE.append({'prompt': prompt, 'tools': names, 'tool_results': len(tool_messages)})
    arguments = {'search_flights': {'origin': 'Mumbai', 'destination': 'Singapore', 'avoid_red_eye': True}, 'search_hotels': {'city': 'Singapore', 'max_price_per_night_inr': 15000, 'style': 'mid'}, 'search_activities': {'city': 'Singapore'}, 'search_restaurants': {'city': 'Singapore'}, 'get_weather': {'city': 'Singapore'}, 'get_travel_tips': {'city': 'Singapore'}, 'convert_currency': {'amount': 100, 'from_currency': 'SGD', 'to_currency': 'INR'}}
    if names and (not tool_messages):
        calls = [{'id': f'call_{i}', 'type': 'function', 'function': {'name': name, 'arguments': json.dumps(arguments[name])}} for i, name in enumerate(names)]
        message = {'role': 'assistant', 'content': None, 'tool_calls': calls}
        finish = 'tool_calls'
    else:
        if 'Read this travel request' in prompt:
            answer = 'FROM: Mumbai\nTO: Singapore\nDAYS: 4\nTRAVELLERS: 2\nBUDGET: mid; hotel under INR 45000\nINTERESTS: food, city views, culture\nHARD RULES: avoid red-eye\nMISSING INFO: dates, return flight, room sharing'
        elif 'Which specialists are needed?' in prompt:
            answer = OFFLINE_WORKERS
        elif prompt.startswith('Find flights'):
            answer = 'TOP 3 OPTIONS: 1. MH-199 Malaysia Airlines 14:20–23:55 INR 19400; 2. 6E-1071 IndiGo 08:30–16:40 INR 21900; 3. SQ-421 Singapore Airlines 11:45–19:50 INR 28500\nRECOMMENDED: 6E-1071, cheapest nonstop daytime option.\nTRADE-OFFS: MH-199 costs less but has a stop.\nASSUMPTIONS: one-way per-person fares, return unavailable.'
        elif prompt.startswith('Find hotels'):
            answer = 'TOP 3 OPTIONS: 1. The Sultan, Kampong Glam, 4.5, INR 11200/night, INR 33600 total; 2. Hotel Mono, Chinatown, 4.4, INR 10500/night, INR 31500 total; 3. Village Hotel Bugis, Bugis, 4.3, INR 9800/night, INR 29400 total\nRECOMMENDED: Hotel Mono for food and culture.\nTRADE-OFFS: lower rating than The Sultan.\nASSUMPTIONS: three nights, one shared room.'
        elif prompt.startswith('Plan the days'):
            answer = 'DAY BY DAY: Day 1 Chinatown Heritage Centre, Hawker food trail, Maxwell Food Centre; Day 2 Gardens by the Bay, SkyPark, Lau Pa Sat; Day 3 Sultan Mosque walk, Little India, Komala Vilas; Day 4 Singapore Flyer, rest, Tiong Bahru Market.\nWEATHER NOTE: allow indoor breaks for afternoon rain.\nASSUMPTIONS: arrival/departure dates and times not confirmed.'
        elif 'Review this plan against' in prompt:
            answer = OFFLINE_CRITIQUE
        elif 'Fix ONLY the problems' in prompt:
            answer = prompt.split('PLAN:\n', 1)[1].split('\nPROBLEMS TO FIX:', 1)[0].strip() + '\nWHAT CHANGED: Explicitly state one-way fares per person; three nights in a shared room.'
        else:
            flight_requested = 'FLIGHT REPORT:\nnot requested' not in prompt
            hotel_requested = 'HOTEL REPORT:\nnot requested' not in prompt
            activity_requested = 'ACTIVITY REPORT:\nnot requested' not in prompt
            activity_report = prompt.split('ACTIVITY REPORT:\n', 1)[1].split('\nUse these headings:', 1)[0].strip()
            total = (43800 if flight_requested else 0) + (31500 if hotel_requested else 0)
            answer = 'CHOSEN FLIGHT: ' + ('6E-1071, INR 43800 for two one-way tickets.' if flight_requested else 'not requested') + '\nCHOSEN HOTEL: ' + ('Hotel Mono, INR 31500 for three nights.' if hotel_requested else 'not requested') + '\nDAY BY DAY PLAN: ' + (activity_report if activity_requested else 'not requested') + f'\nTOTAL COST: INR {total} for requested flight/hotel components; meals, activities, visa and return flights excluded.' + '\nWHY THESE CHOICES: requested options follow specialist recommendations.' + '\nASSUMPTIONS: sample trip; booking dates unconfirmed.'
        message = {'role': 'assistant', 'content': answer}
        finish = 'stop'
    return httpx2.Response(200, json={'id': 'offline-travel', 'object': 'chat.completion', 'created': 0, 'model': MODEL, 'choices': [{'index': 0, 'message': message, 'finish_reason': finish}]})

async def validate():
    from pathlib import Path
    import ast, nbformat, hashlib, io, contextlib, sys, types
    from unittest.mock import patch
    from agent_framework import WorkflowContext
    from agent_framework.openai import OpenAIChatCompletionClient as RealProvider

    root = Path(__file__).resolve().parents[1]
    notebook = root / 'notebooks/travel_planner_microsoft_agent_framework.ipynb'
    n = nbformat.read(notebook, as_version=4)
    nbformat.validate(n)
    ns = {}
    clients, messages, writes = [], [], []
    provider_calls = []

    def provider(**kwargs):
        provider_calls.append(kwargs)
        http = httpx2.AsyncClient(transport=httpx2.MockTransport(offline_response))
        clients.append(http)
        sdk = AsyncOpenAI(api_key='synthetic-validation-key', base_url='https://offline.invalid/v1', http_client=http)
        return RealProvider(model=kwargs['model'], async_client=sdk)

    original_send, original_set = WorkflowContext.send_message, WorkflowContext.set_state
    async def send(ctx, message, *args, **kwargs):
        assert message == 'continue'
        messages.append(message)
        return await original_send(ctx, message, *args, **kwargs)
    def write(ctx, key, value):
        writes.append(key)
        return original_set(ctx, key, value)

    google, colab = types.ModuleType('google'), types.ModuleType('google.colab')
    colab.userdata = types.SimpleNamespace(get=lambda name: 'synthetic-colab-key')
    google.colab = colab
    try:
        with patch.dict(sys.modules, {'google': google, 'google.colab': colab}), patch.dict(os.environ, {}, clear=True), patch('builtins.input', return_value='Plan a 4-day Singapore trip from Mumbai for two people.'), patch.object(WorkflowContext, 'send_message', send), patch.object(WorkflowContext, 'set_state', write), contextlib.redirect_stdout(io.StringIO()) as captured:
            for cell in n.cells:
                if cell.cell_type != 'code' or '%pip' in cell.source:
                    continue
                value = eval(compile(cell.source, 'travel-notebook', 'exec', flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT), ns)
                if value is not None:
                    await value
                # The live setup imports the real provider; intercept its transport before agent construction.
                if 'def read_openai_key' in cell.source:
                    assert os.environ['OPENAI_API_KEY'] == 'synthetic-colab-key'
                    ns['OpenAIChatCompletionClient'] = provider
            assert 'synthetic-colab-key' not in captured.getvalue()
            assert len(provider_calls) == 5
            assert all(k['api_key'] == 'synthetic-colab-key' for k in provider_calls)
            expected_fields = set(ns['TravelState'].__annotations__)
            assert len(expected_fields) == 9 and set(ns['result']) == expected_fields
            assert set(writes) == expected_fields
            assert any(t['tool_results'] == 3 for t in OFFLINE_TRACE)
            assert any(t['tool_results'] == 2 for t in OFFLINE_TRACE)
            assert all('retriver' not in t['tools'] for t in OFFLINE_TRACE)
            global OFFLINE_WORKERS, OFFLINE_CRITIQUE
            OFFLINE_WORKERS = 'flight_agent'
            OFFLINE_CRITIQUE = 'NO ISSUES FOUND.'
            start = len(OFFLINE_TRACE)
            single = await ns['run_travel_state']('flight-only input')
            assert set(single) == expected_fields - {'hotel_report', 'activity_report'}
            assert single['request'] == 'flight-only input'
            assert single['final_plan'] == single['draft_plan']
            trace = OFFLINE_TRACE[start:]
            assert not any('Fix ONLY' in t['prompt'] for t in trace)
            assert next(t['prompt'] for t in trace if 'Write the first version' in t['prompt']).count('not requested') == 2
            OFFLINE_WORKERS = 'hotel_agent, activity_agent'
            pair = await ns['run_travel_state']('hotel/activity input')
            assert 'flight_report' not in pair and 'hotel_report' in pair and 'activity_report' in pair
            OFFLINE_WORKERS = 'unknown'
            fallback = await ns['run_travel_state']('fallback input')
            assert len(fallback['chosen_workers']) == 3
            OFFLINE_WORKERS = 'flight_agent, hotel_agent, activity_agent'
            OFFLINE_CRITIQUE = '1. Clarify fare and stay assumptions.'
            original_ask = ns['ask']
            active = peak = 0
            async def overlap(agent, question):
                nonlocal active, peak
                if question.startswith(('Find flights', 'Find hotels', 'Plan the days')):
                    active += 1
                    peak = max(peak, active)
                    try:
                        await asyncio.sleep(0.02)
                        return await original_ask(agent, question)
                    finally:
                        active -= 1
                if 'Write the first version' in question:
                    assert active == 0
                return await original_ask(agent, question)
            ns['ask'] = overlap
            await ns['run_travel_state']('concurrency test')
            assert peak == 3
            ns['ask'] = original_ask
            one, two = await asyncio.gather(ns['run_travel_state']('independent A'), ns['run_travel_state']('independent B'))
            assert one['request'] == 'independent A' and two['request'] == 'independent B'
            assert 'WHAT CHANGED' in one['final_plan']
            # Optional presentation checkpoint extension also runs only under this intercepted transport.
            checkpoint_example = 'from agent_framework import InMemoryCheckpointStorage, WorkflowBuilder\n\n# OPTIONAL EXTENSION: current notebook does not enable checkpoint storage.\ncheckpoint_storage = InMemoryCheckpointStorage()\n\ndef create_checkpoint_workflow():\n    return (WorkflowBuilder(\n        name="travel-checkpoint-demo",\n        start_executor=manager_step,\n        output_from=[revision_step],\n        checkpoint_storage=checkpoint_storage,\n    ).add_edge(manager_step, workers_step)\n     .add_edge(workers_step, synthesis_step)\n     .add_edge(synthesis_step, critic_step)\n     .add_edge(critic_step, revision_step).build())\n\n# Optional extension using the notebook definitions; validation intercepts HTTP externally.\nrecording = create_checkpoint_workflow()\nrecorded = await recording.run(demo_request)\ncheckpoints = await checkpoint_storage.list_checkpoints(\n    workflow_name="travel-checkpoint-demo")\nworker_checkpoint = next(cp for cp in checkpoints\n    if "activity_report" in cp.state and "draft_plan" not in cp.state)\n\n# Replay from the recorded barrier, using the same graph and storage.\n# This is a completed-run replay, not an intentional pause mechanism.\nrestored = create_checkpoint_workflow()\nresumed = await restored.run(checkpoint_id=str(worker_checkpoint.checkpoint_id))\nfinal_state = resumed.get_outputs()[0]\nassert final_state == recorded.get_outputs()[0]\n'
            checkpoint_result = eval(compile(checkpoint_example, 'checkpoint-extension', 'exec', flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT), ns)
            await checkpoint_result
            assert len(ns['checkpoints']) == 6
            assert ns['worker_checkpoint'].iteration_count == 2
            # Credential failure guidance uses synthetic errors, never real keys.
            for kind, text in [('SecretNotFoundError', 'secret missing'), ('NotebookAccessError', 'access denied'), ('TimeoutException', 'Secrets unavailable')]:
                def fail(name, kind=kind):
                    raise type(kind, (Exception,), {})('sensitive-placeholder')
                colab.userdata.get = fail
                os.environ['OPENAI_API_KEY'] = 'synthetic-env-key'
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    try:
                        ns['read_openai_key']()
                    except RuntimeError as error:
                        assert 'Notebook access' in str(error)
                    else:
                        raise AssertionError('Denied Colab secret should fail clearly')
                assert output.getvalue() == ''
                assert 'sensitive-placeholder' not in output.getvalue()
                assert 'synthetic-env-key' not in output.getvalue()
            # Source fidelity: data, tools and all business-stage prompt literals.
            old = nbformat.read(root / 'notebooks/travel_planner_langgraph_(1) (2).ipynb', as_version=4)
            assert hashlib.sha256((root / 'notebooks/travel_planner_langgraph_(1) (2).ipynb').read_bytes()).hexdigest() == n.metadata.source_notebook_sha256
            code_cells = [c.source for c in n.cells if c.cell_type == 'code']
            assert old.cells[7].source in code_cells
            def funcs(source):
                return {x.name: ast.dump(x, include_attributes=False) for x in ast.parse(source).body if isinstance(x, ast.FunctionDef)}
            tools = next(c for c in code_cells if 'def search_flights' in c)
            assert funcs(old.cells[9].source) == funcs(tools)
            def literals(source):
                return sorted(x.value for x in ast.walk(ast.parse(source)) if isinstance(x, ast.Constant) and isinstance(x.value, str))
            nodes = next(c for c in code_cells if 'async def manager_step' in c)
            assert 'read_travel_state' not in nodes and 'write_travel_update' not in nodes
            actual = ast.parse(nodes)
            assert {x.name for x in actual.body if isinstance(x, ast.AsyncFunctionDef)} == {
                'manager_step', 'workers_step', 'synthesis_step', 'critic_step', 'revision_step'}
            # Direct executor refactor retains the manager/review prompt text.
            # Worker prompts are assembled from the same instruction + requirements.
            def prompt_texts(tree):
                return [tuple(x.value for x in node.values if isinstance(x, ast.Constant) and isinstance(x.value, str))
                        for node in ast.walk(tree) if isinstance(node, ast.JoinedStr)]
            original = ast.parse(old.cells[19].source)
            original_prompts = prompt_texts(ast.Module(body=[x for x in original.body
                if isinstance(x, ast.FunctionDef) and x.name not in ('flight_node', 'hotel_node', 'activity_node')], type_ignores=[]))
            for prompt in original_prompts:
                assert prompt in prompt_texts(actual), prompt
            assert all(text in literals(nodes) for text in [
                'Find flights for this trip.', 'Find hotels for this trip.', 'Plan the days for this trip.'])
            # Exact instruction strings and sample request, with no invented seed/settings.
            original_agents = ast.parse(old.cells[15].source)
            current_agents = ast.parse(next(c for c in code_cells if 'async def ask' in c))
            original_prompts = [ast.literal_eval(k.value) for x in ast.walk(original_agents) if isinstance(x, ast.Call) for k in x.keywords if k.arg == 'system_prompt']
            current_prompts = [ast.literal_eval(k.value) for x in ast.walk(current_agents) if isinstance(x, ast.Call) for k in x.keywords if k.arg == 'instructions']
            assert original_prompts == current_prompts
            original_sample = next(x.value for x in ast.parse(old.cells[27].source).body if isinstance(x, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'demo_request' for t in x.targets))
            assert ns['demo_request'] == ast.literal_eval(original_sample)
            assert ns['MODEL'] == 'gpt-4o-mini'
            assert not any('OFFLINE_DEMO' in c for c in code_cells)
    finally:
        for http in clients:
            await http.aclose()
    print('PASS: every live notebook cell with intercepted HTTP; actual Agents/tools/workflow; 1/2/3 workers/fallback; revision branches; native state/control signals; parallel barrier; isolated runs; Secrets; source fidelity. No paid calls.')

if __name__ == '__main__':
    asyncio.run(validate())
