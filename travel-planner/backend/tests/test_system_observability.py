"""Telemetry shape, privacy and streaming checks; no cloud calls."""
import asyncio
import io
import json
import logging
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.event_log import JsonFormatter, logger, observed
from app.process_metrics import process_cpu, process_memory
from app.system_observability import RequestObserver


class SystemObservabilityTests(unittest.TestCase):
    def test_node_and_tool_logs_have_timing_without_arguments_or_results(self):
        output = io.StringIO()
        handler = logging.StreamHandler(output)
        handler.setFormatter(JsonFormatter())

        @observed('tool')
        def example(secret):
            return 'private result'

        with patch.object(logger, 'handlers', [handler]), patch.object(logger, 'level', logging.INFO):
            self.assertEqual(example('private input'), 'private result')
        rows = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual([row['event'] for row in rows], ['tool.start', 'tool.finish'])
        self.assertEqual(rows[-1]['outcome'], 'success')
        self.assertEqual(rows[-1]['level'], 30)
        self.assertIn('duration_ms', rows[-1])
        self.assertNotIn('private', output.getvalue())

    def test_failures_log_only_error_type_and_still_raise(self):
        @observed('node')
        def broken():
            raise ValueError('private provider detail')

        with self.assertLogs(logger, level=logging.INFO) as captured, self.assertRaises(ValueError):
            broken()
        record = captured.records[-1]
        self.assertEqual(record.fields['error_type'], 'ValueError')
        self.assertEqual(record.fields['outcome'], 'error')
        self.assertNotIn('private provider detail', JsonFormatter().format(record))

    def test_metrics_describe_only_the_current_process(self):
        self.assertGreaterEqual(process_cpu(None)[0].value, 0)
        self.assertGreater(process_memory(None)[0].value, 0)

    def test_http_observer_forwards_chunks_before_request_completion(self):
        delivered = []
        counter = Mock()

        async def fake_app(scope, receive, send):
            await send({'type': 'http.response.start', 'status': 200})
            await send({'type': 'http.response.body', 'body': b'private first chunk', 'more_body': True})
            self.assertEqual(len(delivered), 2)
            await send({'type': 'http.response.body', 'body': b'last', 'more_body': False})

        async def send(message):
            delivered.append(message)

        scope = {'type': 'http', 'method': 'POST', 'route': SimpleNamespace(path='/api/plan'),
                 'app': SimpleNamespace(state=SimpleNamespace(request_count=counter))}
        with patch('app.system_observability.log_event') as log:
            asyncio.run(RequestObserver(fake_app)(scope, None, send))
        self.assertEqual(len(delivered), 3)
        counter.add.assert_called_once_with(1, {'app': 'travel-planner', 'method': 'POST',
                                               'route': '/api/plan', 'status_code': '200'})
        self.assertNotIn('private first chunk', str(log.call_args))
