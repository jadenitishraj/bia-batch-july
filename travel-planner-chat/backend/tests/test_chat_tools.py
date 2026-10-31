import unittest
from unittest.mock import patch
from urllib.error import URLError

from chat_support import TRIP, ChatServer
from langchain_core.tools import ToolException
from trip_tools import make_trip_tools, trip_request


class ToolTests(unittest.TestCase):
    def test_three_tools_use_real_trip_endpoints_and_preserve_other_fields(self):
        with ChatServer() as api:
            tools = make_trip_tools(api.base, api.token)
            self.assertEqual([tool.name for tool in tools],
                             ['create_trip', 'update_trip', 'delete_trip'])
            create, update, delete = tools
            self.assertNotIn('token', create.args)
            saved = create.invoke(TRIP)
            self.assertEqual(api.call('/api/trips')[1][0]['id'], saved['id'])
            changed = update.invoke({'trip_id': saved['id'], 'budget': 25000})
            self.assertEqual(changed['budget'], 25000)
            self.assertEqual(changed['plan'], TRIP['plan'])
            self.assertEqual(changed['destination'], TRIP['destination'])
            self.assertEqual(delete.invoke({'trip_id': saved['id']}), {'deleted': True})
            self.assertEqual(api.call('/api/trips')[1], [])
            with self.assertRaisesRegex(ToolException, 'Trip not found'):
                update.invoke({'trip_id': saved['id'], 'title': 'Missing'})

    def test_tools_cannot_update_or_delete_another_accounts_trip(self):
        with ChatServer() as api:
            create, _, _ = make_trip_tools(api.base, api.token)
            saved = create.invoke(TRIP)
            other_token = api.register('two@example.test')
            _, update, delete = make_trip_tools(api.base, other_token)
            for tool, values in [(update, {'trip_id': saved['id'], 'title': 'Stolen'}),
                                 (delete, {'trip_id': saved['id']})]:
                with self.assertRaisesRegex(ToolException, 'Trip not found'):
                    tool.invoke(values)
            self.assertEqual(api.call('/api/trips')[1][0]['title'], TRIP['title'])
            create, _, _ = make_trip_tools(api.base, 'Bearer invalid')
            with self.assertRaisesRegex(ToolException, 'log in again'):
                create.invoke(TRIP)

    def test_validation_and_network_failures_are_safe(self):
        with ChatServer() as api:
            create, _, _ = make_trip_tools(api.base, api.token)
            with self.assertRaises(ToolException):
                create.invoke({**TRIP, 'days': 0})
            self.assertEqual(api.call('/api/trips')[1], [])
        for error in (URLError('offline'), TimeoutError()):
            with patch('trip_tools.urlopen', side_effect=error):
                with self.assertRaisesRegex(ToolException, 'Check your trips'):
                    trip_request('http://127.0.0.1:1', 'Bearer private')
