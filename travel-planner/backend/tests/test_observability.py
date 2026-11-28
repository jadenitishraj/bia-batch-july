"""Verify opt-in trace privacy, nesting and streaming without external services."""
import asyncio
import json
import os
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from app.main import app
from app.observability import demo_client, demo_events
from fastapi.testclient import TestClient
from langchain_core.runnables import RunnableLambda
from langsmith import get_current_run_tree, tracing_context


class ObservabilityTests(unittest.TestCase):
    def test_demo_is_disabled_without_its_dedicated_key(self):
        with patch.dict(os.environ, {}, clear=True), patch('app.observability.Client') as client:
            response = TestClient(app).post('/api/observability/demo')
        self.assertEqual(response.status_code, 503)
        client.assert_not_called()

    def test_client_hides_all_nested_payloads(self):
        env = {'TRAVEL_PLANNER_LANGSMITH_API_KEY': 'private-test-token',
               'GOOGLE_API_KEY': 'private-google-token'}
        with patch.dict(os.environ, env, clear=True), patch('app.observability.Client') as client:
            demo_client()
        options = client.call_args.kwargs
        for name in ('hide_inputs', 'hide_outputs', 'hide_metadata'):
            self.assertTrue(options[name])

    def test_ordinary_stream_overrides_global_and_parent_tracing(self):
        seen = []

        def classify(_):
            from app.document_answers import RequestIntent
            from langsmith.run_helpers import get_tracing_context
            seen.append(get_tracing_context()['enabled'])
            return RequestIntent(travel=False, documents=False)

        with patch.dict(os.environ, {'LANGSMITH_TRACING': 'true'}), tracing_context(
            enabled=True
        ), patch('app.main.classify_request', side_effect=classify):
            response = TestClient(app).post('/api/plan', json={'request': 'Find sample Singapore flights'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(seen, [False])

    def test_live_graph_boundary_keeps_children_nested_and_streams_final_answer(self):
        roots = []
        children = []

        def record_child(value):
            child = get_current_run_tree()
            children.append(child)
            return value

        class FakeGraph:
            async def astream(self, state, **kwargs):
                roots.append(get_current_run_tree())
                self.request = state['request']
                await RunnableLambda(record_child).ainvoke(state)
                yield {'revision': {'final_plan': 'Synthetic final plan'}}

        client = Mock()
        graph = FakeGraph()
        run_id = uuid4()

        async def check():
            return [json.loads(line) async for line in demo_events(client, run_id, 'test-project')]

        with patch('app.graph.travel_planner', graph):
            events = asyncio.run(check())
        self.assertIn('sample travel data', graph.request)
        self.assertEqual(roots[0].id, run_id)
        self.assertEqual(roots[0].name, 'Travel Planner classroom workflow')
        self.assertEqual(children[0].parent_run_id, run_id)
        self.assertIn({'type': 'result', 'answer': 'Synthetic final plan'}, events)
        self.assertIn({'type': 'done'}, events)
        self.assertEqual(events[-1]['run_id'], str(run_id))
        client.flush.assert_called_once_with(timeout=10)

    def test_failed_graph_marks_trace_failed_and_does_not_leak_error(self):
        roots = []

        class BrokenGraph:
            async def astream(self, *args, **kwargs):
                roots.append(get_current_run_tree())
                raise RuntimeError('private provider detail')
                yield

        async def check():
            return [json.loads(line) async for line in demo_events(Mock(), uuid4(), 'test-project')]

        with patch('app.graph.travel_planner', BrokenGraph()):
            events = asyncio.run(check())
        self.assertIsNotNone(roots[0].error)
        self.assertNotIn('private provider detail', str(events))
        self.assertTrue(any(event['type'] == 'error' for event in events))
        self.assertFalse(any(event['type'] == 'done' for event in events))
