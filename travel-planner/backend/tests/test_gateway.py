"""Exercise the real gateway adapter and tool loop without external model calls."""
import json
import os
import unittest
from unittest.mock import patch

import httpx
from app.gateway import GatewayChatOpenAI
from app.main import app
from app.models import create_model, is_configured
from app.tools import search_flights
from fastapi.testclient import TestClient
from langchain.agents import create_agent
from openai import RateLimitError


class GatewayTests(unittest.TestCase):
    def test_gateway_factory_is_explicit_private_and_does_not_forward_provider_keys(self):
        settings = {'CHAT_PROVIDER': 'helicone', 'HELICONE_API_KEY': 'gateway-test-key',
                    'GOOGLE_API_KEY': 'google-private-key', 'OPENAI_API_KEY': 'openai-private-key'}
        with patch.dict(os.environ, settings, clear=True), patch('app.gateway.GatewayChatOpenAI') as model:
            self.assertTrue(is_configured())
            self.assertIs(create_model('manager'), model.return_value)
            options = model.call_args.kwargs
            self.assertEqual(options['api_key'], 'gateway-test-key')
            self.assertEqual(options['model'], 'gemini-3.1-flash-lite/google-ai-studio')
            self.assertEqual(options['base_url'], 'https://ai-gateway.helicone.ai/v1')
            headers = options['default_headers']
            self.assertEqual(headers['Helicone-Property-Agent'], 'manager')
            self.assertEqual(headers['Helicone-Omit-Request'], 'true')
            self.assertEqual(headers['Helicone-Omit-Response'], 'true')
            self.assertNotIn('Helicone-RateLimit-Policy', headers)
            self.assertNotIn('google-private-key', str(options))
            self.assertNotIn('openai-private-key', str(options))
        with patch.dict(os.environ, {'CHAT_PROVIDER': 'helicone'}, clear=True):
            self.assertFalse(is_configured())
            with self.assertRaises(ValueError):
                create_model()

    def test_actual_openai_compatible_adapter_executes_a_specialist_tool(self):
        requests = []

        def respond(request):
            requests.append(request)
            if len(requests) == 1:
                message = {'role': 'assistant', 'content': None, 'tool_calls': [{
                    'id': 'flight-call', 'type': 'function', 'function': {
                        'name': 'search_flights', 'arguments': json.dumps({
                            'origin': 'Mumbai', 'destination': 'Singapore',
                            'avoid_red_eye': True, 'max_price_inr': 25000})}}]}
                finish = 'tool_calls'
            else:
                message = {'role': 'assistant', 'content': 'Two sample flight options found.'}
                finish = 'stop'
            openai_response = {
                'id': 'demo-response', 'object': 'chat.completion', 'created': 1,
                'model': 'gateway-test-model', 'choices': [
                    {'index': 0, 'message': message, 'finish_reason': finish}],
                'usage': {'prompt_tokens': 20, 'completion_tokens': 10, 'total_tokens': 30}}
            # The live BYOK gateway returns native Gemini JSON for unregistered models.
            parts = [{'functionCall': {'name': 'search_flights', 'args': {
                'origin': 'Mumbai', 'destination': 'Singapore',
                'avoid_red_eye': True, 'max_price_inr': 25000}}}] if len(requests) == 1 else [
                    {'text': 'Two sample flight options found.'}]
            native_response = {'candidates': [{'content': {'role': 'model', 'parts': parts},
                                               'finishReason': 'STOP'}],
                               'usageMetadata': {'serviceTier': 'standard', 'promptTokenCount': 20,
                                                 'candidatesTokenCount': 10,
                                                 'totalTokenCount': 30}}
            return httpx.Response(200, json=native_response if len(requests) == 1 else openai_response,
                headers={'helicone-id': 'synthetic-request-id'})

        with httpx.Client(transport=httpx.MockTransport(respond)) as client:
            def construct(**kwargs):
                return GatewayChatOpenAI(**kwargs, http_client=client)

            with patch.dict(os.environ, {'CHAT_PROVIDER': 'helicone',
                                        'HELICONE_API_KEY': 'gateway-test-key'}, clear=True), patch(
                'app.gateway.GatewayChatOpenAI', side_effect=construct
            ):
                agent = create_agent(model=create_model('flight_agent'), tools=[search_flights])
                result = agent.invoke({'messages': [('user', 'Find sample Singapore flights')]})
        self.assertEqual(result['messages'][-1].text, 'Two sample flight options found.')
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[0].url.host, 'ai-gateway.helicone.ai')
        self.assertEqual(requests[0].headers['authorization'], 'Bearer gateway-test-key')
        messages = json.loads(requests[1].content)['messages']
        tool_message = next(message for message in messages if message['role'] == 'tool')
        self.assertIn('MH-199', tool_message['content'])
        self.assertNotIn('AI-342', tool_message['content'])

    def test_model_selection_and_safe_429_handling(self):
        settings = {'CHAT_PROVIDER': 'helicone', 'HELICONE_API_KEY': 'gateway-test-key',
                    'HELICONE_MODEL': 'gpt-4o-mini/openai'}
        with patch.dict(os.environ, settings, clear=True), patch('app.gateway.GatewayChatOpenAI') as model:
            create_model()
            self.assertEqual(model.call_args.kwargs['model'], 'gpt-4o-mini/openai')
            self.assertEqual(model.call_args.kwargs['max_retries'], 0)
            self.assertNotIn('Helicone-RateLimit-Policy', model.call_args.kwargs['default_headers'])
        response = httpx.Response(429, request=httpx.Request('POST', 'https://ai-gateway.helicone.ai/v1/chat/completions'))
        error = RateLimitError('private provider details', response=response, body=None)
        with patch('app.main.classify_request', side_effect=error):
            response = TestClient(app).post('/api/plan', json={'request': 'Find Singapore flights'})
        self.assertIn('rate limit or quota', response.text)
        self.assertNotIn('private provider details', response.text)
