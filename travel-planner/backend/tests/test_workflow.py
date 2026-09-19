"""Offline regression checks; never call the AI provider."""
import json
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.graph import travel_planner
from app.tools import search_flights


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        from app.document_answers import RequestIntent
        routing = patch('app.main.classify_request', return_value=RequestIntent(travel=True, documents=False))
        routing.start()
        self.addCleanup(routing.stop)

    def test_flights_respect_constraints(self):
        flights = search_flights.invoke({'origin': 'Mumbai', 'destination': 'Singapore', 'avoid_red_eye': True, 'max_price_inr': 25000})
        self.assertEqual([f['id'] for f in flights], ['MH-199', '6E-1071'])

    def test_selected_workers_join_before_one_synthesis(self):
        for selection in ['flight_agent', 'flight_agent, hotel_agent, activity_agent']:
            calls = []
            def fake_ask(agent, question):
                calls.append(question)
                if 'Which specialists' in question:
                    return selection
                if 'Review this plan' in question:
                    return 'NO ISSUES FOUND'
                if 'Write the first version' in question:
                    return 'Exact final plan'
                return 'Worker information'
            with patch('app.nodes.ask', side_effect=fake_ask):
                result = travel_planner.invoke({'request': 'Singapore trip'})
            self.assertEqual(result['final_plan'], 'Exact final plan')
            self.assertEqual(sum('Write the first version' in q for q in calls), 1)
            self.assertEqual('hotel_report' in result, 'hotel_agent' in selection)
            self.assertEqual('activity_report' in result, 'activity_agent' in selection)

    def test_stream_returns_exact_final_plan(self):
        class FakeGraph:
            async def astream(self, *args, **kwargs):
                yield {'revision': {'final_plan': '# Exact answer\n₹45,000'}}
        with patch('app.graph.travel_planner', FakeGraph()):
            response = TestClient(app).post('/api/plan', json={'request': 'Plan Singapore'})
        events = [json.loads(line) for line in response.text.splitlines()]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(next(e['answer'] for e in events if e['type'] == 'result'), '# Exact answer\n₹45,000')
        self.assertEqual(events[-1]['type'], 'done')

    def test_error_does_not_leak_provider_payload(self):
        class FakeGraph:
            async def astream(self, *args, **kwargs):
                raise RuntimeError('private provider payload')
                yield
        with patch('app.graph.travel_planner', FakeGraph()):
            response = TestClient(app).post('/api/plan', json={'request': 'Plan Singapore'})
        self.assertNotIn('private provider payload', response.text)
        self.assertEqual(json.loads(response.text.splitlines()[-1])['type'], 'error')

    def test_short_request_rejected(self):
        self.assertEqual(TestClient(app).post('/api/plan', json={'request': ''}).status_code, 422)


if __name__ == '__main__':
    unittest.main()
