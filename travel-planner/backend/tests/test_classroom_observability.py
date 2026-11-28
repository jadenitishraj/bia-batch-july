"""Offline checks for the short classroom integrations; no cloud/model calls."""
import importlib
import json
import os
import unittest
from unittest.mock import Mock, patch

import httpx
from app import models
from app.logger import logger
from app.main import app
from app.tools import search_flights
from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain.agents import create_agent
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import get_current_run_tree, tracing_context
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader


class ClassroomObservabilityTests(unittest.TestCase):
    def test_proxy_is_default_when_key_exists_and_missing_key_uses_google_directly(self):
        try:
            for key, expected in [('test-helicone-key', 'https://gateway.helicone.ai'), ('', None)]:
                with patch.dict(os.environ, {'HELICONE_API_KEY': key}), patch(
                    'langchain_google_genai.ChatGoogleGenerativeAI'
                ) as constructor:
                    importlib.reload(models)
                    options = constructor.call_args.kwargs
                    self.assertEqual(options['base_url'], expected)
                    self.assertFalse(any('Agent' in name for name in options['additional_headers']))
                    self.assertEqual(bool(options['additional_headers']), bool(key))
                    if key:
                        self.assertEqual(options['additional_headers']['Helicone-Omit-Request'], 'true')
                        self.assertEqual(options['additional_headers']['Helicone-Omit-Response'], 'true')
        finally:
            importlib.reload(models)

    def test_native_gemini_proxy_executes_a_real_tool_loop_without_custom_parser(self):
        requests = []

        def respond(request):
            requests.append(request)
            part = {'functionCall': {'name': 'search_flights', 'args': {
                'origin': 'Mumbai', 'destination': 'Singapore', 'avoid_red_eye': True,
                'max_price_inr': 25000}}} if len(requests) == 1 else {'text': 'Two sample flights found.'}
            return httpx.Response(200, json={'candidates': [{'content': {'role': 'model', 'parts': [part]},
                'finishReason': 'STOP'}], 'usageMetadata': {'promptTokenCount': 20,
                'candidatesTokenCount': 10, 'totalTokenCount': 30}})

        model = ChatGoogleGenerativeAI(model='gemini-3.1-flash-lite', api_key='fake-google-key',
            base_url='https://gateway.helicone.ai', vertexai=False, max_retries=0,
            additional_headers={'Helicone-Auth': 'Bearer fake-helicone-key',
                                'Helicone-Target-URL': 'https://generativelanguage.googleapis.com'},
            client_args={'transport': httpx.MockTransport(respond)})
        agent = create_agent(model=model, tools=[search_flights])
        result = agent.invoke({'messages': [('user', 'Find sample Singapore flights')]})
        self.assertEqual(result['messages'][-1].text, 'Two sample flights found.')
        self.assertEqual(len(requests), 2)
        self.assertTrue(all(request.url.host == 'gateway.helicone.ai' for request in requests))
        self.assertIn('MH-199', requests[1].content.decode())
        self.assertNotIn('AI-342', requests[1].content.decode())

    def test_tool_logs_do_not_include_arguments_or_results(self):
        with self.assertLogs(logger, level='INFO') as captured:
            search_flights.invoke({'origin': 'private-input', 'destination': 'Singapore'})
        self.assertIn('search_flights started', str(captured.output))
        self.assertNotIn('private-input', str(captured.output))

    def test_actual_api_stream_keeps_nested_langsmith_runs(self):
        from app.document_answers import RequestIntent
        roots, children = [], []

        def child(value):
            children.append(get_current_run_tree())
            return value

        class Graph:
            async def astream(self, *args, **kwargs):
                roots.append(get_current_run_tree())
                await RunnableLambda(child).ainvoke({})
                yield {'revision': {'final_plan': 'Fixed sample answer'}}

        with tracing_context(enabled=True, client=Mock(), project_name='offline-test'), patch(
            'app.main.classify_request', return_value=RequestIntent(travel=True, documents=False)
        ), patch('app.graph.travel_planner', Graph()):
            response = TestClient(app).post('/api/plan', json={'request': 'Find sample flights'})
        self.assertEqual(roots[0].name, 'Travel Planner')
        self.assertEqual(children[0].parent_run_id, roots[0].id)
        events = [json.loads(line) for line in response.text.splitlines()]
        self.assertIn({'type': 'result', 'answer': 'Fixed sample answer'}, events)

    def test_packages_collect_api_cpu_and_current_memory_metrics(self):
        reader = InMemoryMetricReader()
        provider = MeterProvider(metric_readers=[reader])
        process = SystemMetricsInstrumentor(config={'process.cpu.time': ['user', 'system'],
                                                    'process.memory.usage': None})
        demo = FastAPI()
        demo.get('/health')(lambda: {'ok': True})
        FastAPIInstrumentor.instrument_app(demo, meter_provider=provider)
        process.instrument(meter_provider=provider)
        try:
            self.assertEqual(TestClient(demo).get('/health').status_code, 200)
            data = reader.get_metrics_data()
            metrics = {metric.name: metric for resource in data.resource_metrics
                       for scope in resource.scope_metrics for metric in scope.metrics}
            self.assertGreater(metrics['process.memory.usage'].data.data_points[0].value, 0)
            self.assertGreaterEqual(metrics['process.cpu.time'].data.data_points[0].value, 0)
            self.assertEqual(metrics['http.server.duration'].data.data_points[0].count, 1)
        finally:
            process.uninstrument()
            FastAPIInstrumentor.uninstrument_app(demo)
            provider.shutdown()
