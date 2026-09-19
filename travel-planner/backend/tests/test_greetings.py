import json
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

class GreetingTests(unittest.TestCase):
    def test_hi_answers_without_model_or_retrieval(self):
        with patch('app.main.classify_request') as classify, patch('app.main.answer_documents') as retrieve:
            for message in ['hi', ' Hi! ', 'hello', 'hey']:
                response = TestClient(app).post('/api/plan', json={'request': message})
                self.assertEqual(response.status_code, 200)
                events = [json.loads(line) for line in response.text.splitlines()]
                self.assertIn('Hi!', events[1]['answer'])
                self.assertEqual(events[-1]['type'], 'done')
            classify.assert_not_called()
            retrieve.assert_not_called()

    def test_whitespace_rejected(self):
        self.assertEqual(TestClient(app).post('/api/plan', json={'request':'   '}).status_code, 422)
