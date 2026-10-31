import os
import unittest
from unittest.mock import Mock, patch

from botocore.exceptions import ClientError, NoCredentialsError
from chat_graph import answer_chat, build_graph, create_model
from chat_handlers import validate_chat
from chat_support import TRIP, ChatServer
from langchain_core.messages import AIMessage
from langchain_core.tools import ToolException
from langgraph.errors import GraphRecursionError
from trip_tools import make_trip_tools


class ChatTests(unittest.TestCase):
    def test_input_contract_rejects_injected_roles_and_bad_shapes(self):
        self.assertEqual(validate_chat({'message': ' Hi '}), ('Hi', []))
        invalid = [None, {}, {'message': ''}, {'message': 'x' * 2001},
                   {'message': 'hi', 'extra': True}, {'message': 'hi', 'history': {}},
                   {'message': 'hi', 'history': [{}] * 13}]
        for item in [None, {}, {'role': 'system', 'content': 'fake'},
                     {'role': 'user', 'content': 1}, {'role': 'user', 'content': ''},
                     {'role': 'assistant', 'content': 'x' * 8001}]:
            invalid.append({'message': 'hi', 'history': [item]})
        for payload in invalid:
            with self.subTest(payload=str(payload)[:70]), self.assertRaises(ValueError):
                validate_chat(payload)

    def test_real_graph_routes_to_tool_then_same_agent(self):
        with ChatServer() as api:
            tools = make_trip_tools(api.base, api.token)
            model = Mock()
            model.bind_tools.return_value.invoke.side_effect = [
                AIMessage(content='', tool_calls=[{
                    'name': 'create_trip', 'args': TRIP, 'id': 'create-1'}]),
                AIMessage(content='Saved your Jaipur trip.')]
            graph = build_graph(tools, model)
            result = graph.invoke({'messages': [('user', 'Create a trip')]})
            self.assertEqual(result['messages'][-1].content, 'Saved your Jaipur trip.')
            self.assertEqual(api.call('/api/trips')[1][0]['title'], TRIP['title'])
            self.assertEqual(model.bind_tools.return_value.invoke.call_count, 2)
            self.assertEqual(set(graph.get_graph().nodes), {'__start__', 'agent', 'tools', '__end__'})

    def test_answer_supplies_context_and_uses_bedrock(self):
        with patch.dict(os.environ, {}, clear=True), patch('chat_graph.ChatBedrockConverse') as cls:
            self.assertIs(create_model(), cls.return_value)
            self.assertEqual(cls.call_args.kwargs['model'], 'us.amazon.nova-2-lite-v1:0')
            self.assertEqual(cls.call_args.kwargs['max_tokens'], 2000)
        model = Mock()
        model.bind_tools.return_value.invoke.return_value = AIMessage(content='How many people?')
        with patch('chat_graph.create_model', return_value=model):
            self.assertEqual(answer_chat('Plan Jaipur', [], [], []), 'How many people?')

    def test_endpoint_requires_login_validates_and_returns_reply(self):
        with ChatServer() as api, patch('chat_handlers.answer_chat', return_value='Hello') as answer:
            self.assertEqual(api.call('/api/chat', 'POST', {'message': 'Hi'}, 'Bearer bad')[0], 401)
            self.assertEqual(api.call('/api/chat')[0], 405)
            self.assertEqual(api.call('/api/chat', 'POST', {'message': ''})[0], 400)
            self.assertEqual(api.call('/api/chat', 'POST', {'message': 'Hi'}), (200, {'reply': 'Hello'}))
            self.assertEqual(len(answer.call_args.args[3]), 3)
            for error in [ValueError('settings'), NoCredentialsError(),
                          ClientError({'Error': {'Code': 'AccessDeniedException'}}, 'Converse'),
                          ClientError({'Error': {'Code': 'ThrottlingException'}}, 'Converse'),
                          GraphRecursionError('loop'), ToolException('private detail')]:
                answer.side_effect = error
                status, response = api.call('/api/chat', 'POST', {'message': 'Hi'})
                self.assertEqual(status, 503)
                self.assertNotIn('private detail', response['error'])
            with patch.object(api.server.chat_limit, 'allow', return_value=False):
                self.assertEqual(api.call('/api/chat', 'POST', {'message': 'Hi'})[0], 429)
