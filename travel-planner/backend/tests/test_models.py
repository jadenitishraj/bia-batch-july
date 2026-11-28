"""Offline checks for Gemini selection, routing and safe provider failures."""
import os
import unittest
from unittest.mock import Mock, patch

from app.main import app
from app.models import create_model, is_configured
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from langchain_google_genai.chat_models import GoogleAuthenticationError


class ModelTests(unittest.TestCase):
    def test_gemini_configuration_and_model_are_separate_from_openai(self):
        env = {'CHAT_PROVIDER': 'gemini', 'GEMINI_API_KEY': 'test-key'}
        with patch.dict(os.environ, env, clear=True), patch(
            'app.models.ChatGoogleGenerativeAI'
        ) as model:
            self.assertTrue(is_configured())
            self.assertIs(create_model(), model.return_value)
            options = model.call_args.kwargs
            self.assertEqual(options['model'], 'gemini-3.1-flash-lite')
            self.assertEqual(options['api_key'], 'test-key')
            self.assertIs(options['vertexai'], False)
            self.assertEqual(options['max_retries'], 0)
        env.update(GOOGLE_API_KEY='primary-test-key', GEMINI_MODEL='chosen-model')
        with patch.dict(os.environ, env, clear=True), patch(
            'app.models.ChatGoogleGenerativeAI'
        ) as model:
            create_model()
            self.assertEqual(model.call_args.kwargs['model'], 'chosen-model')
            self.assertEqual(model.call_args.kwargs['api_key'], 'primary-test-key')

    def test_original_provider_and_missing_or_invalid_settings(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}, clear=True), patch(
            'app.models.ChatOpenAI'
        ) as model:
            self.assertTrue(is_configured())
            self.assertIs(create_model(), model.return_value)
            self.assertEqual(model.call_args.kwargs['model'], 'gpt-4o-mini')
        for provider in ['gemini', 'unsupported']:
            with patch.dict(os.environ, {'CHAT_PROVIDER': provider}, clear=True):
                self.assertFalse(is_configured())
                with self.assertRaises(ValueError):
                    create_model()
                client = TestClient(app)
                self.assertFalse(client.get('/api/health').json()['configured'])
                self.assertEqual(client.post('/api/plan', json={'request': 'Plan Singapore'}).status_code, 503)

    def test_agent_and_document_answers_normalize_gemini_content_blocks(self):
        from app.agents import ask
        from app.document_answers import (
            RequestIntent,
            answer_documents,
            classify_request,
        )
        message = AIMessage(content=[{'type': 'text', 'text': 'Plain answer'}])
        agent = Mock()
        agent.invoke.return_value = {'messages': [message]}
        self.assertEqual(ask(agent, 'Question'), 'Plain answer')
        model = Mock()
        model.invoke.return_value = message
        model.with_structured_output.return_value.invoke.return_value = RequestIntent(
            travel=True, documents=False)
        with patch('app.document_answers.create_model', return_value=model), patch(
            'app.document_answers.retrieve', return_value='Document evidence'
        ):
            self.assertTrue(classify_request('Plan Singapore').travel)
            self.assertEqual(answer_documents('Question'),
                             {'answer': 'Plain answer', 'context': 'Document evidence'})

    def test_gemini_auth_error_does_not_expose_provider_details(self):
        with patch('app.main.classify_request', side_effect=GoogleAuthenticationError('private-key')):
            response = TestClient(app).post('/api/plan', json={'request': 'Plan Singapore'})
        self.assertIn('Gemini key was rejected', response.text)
        self.assertNotIn('private-key', response.text)
