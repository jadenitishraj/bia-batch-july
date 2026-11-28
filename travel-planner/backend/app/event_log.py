"""One standard Python logger: Pino-style JSON locally and in Loki."""
import json
import logging
import os
import time
from functools import wraps
from logging.handlers import QueueHandler, QueueListener
from queue import Queue

import httpx

logger = logging.getLogger('travel_planner')
logger.addHandler(logging.NullHandler())


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({'level': record.levelno + 10, 'time': int(record.created * 1000),
                           'pid': record.process, 'msg': record.getMessage(),
                           **getattr(record, 'fields', {})})


class LokiHandler(logging.Handler):
    def emit(self, record):
        try:
            response = httpx.post(
                os.environ['GRAFANA_LOKI_URL'],
                auth=(os.environ['GRAFANA_LOKI_USER'], os.environ['GRAFANA_CLOUD_TOKEN']),
                json={'streams': [{'stream': {'app': 'travel-planner'},
                                   'values': [[str(int(record.created * 1e9)), self.format(record)]]}]},
                timeout=3,
            )
            self.last_status = response.status_code
        except httpx.HTTPError:
            self.last_status = 'connection_error'


def configure_logging():
    console = logging.StreamHandler()
    handlers = [console]
    if all(os.getenv(key) for key in ('GRAFANA_LOKI_URL', 'GRAFANA_LOKI_USER', 'GRAFANA_CLOUD_TOKEN')):
        handlers.append(LokiHandler())
    for handler in handlers:
        handler.setFormatter(JsonFormatter())
    queue = Queue()
    logger.handlers = [QueueHandler(queue)]
    logger.setLevel(logging.INFO)
    logger.propagate = False
    listener = QueueListener(queue, *handlers)
    listener.start()
    return listener


def log_event(event, **fields):
    # Call sites pass decisions/counts only, never prompts, arguments or result text.
    level = logging.ERROR if fields.get('outcome') == 'error' else logging.INFO
    logger.log(level, event, extra={'fields': {'event': event, **fields}})


def observed(kind):
    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            name = function.__name__
            identity = {'tool' if kind == 'tool' else 'agent': name}
            started = time.perf_counter()
            log_event(kind + '.start', **identity)
            try:
                result = function(*args, **kwargs)
            except Exception as error:
                log_event(kind + '.finish', **identity, outcome='error',
                          error_type=type(error).__name__,
                          duration_ms=round((time.perf_counter() - started) * 1000, 2))
                raise
            log_event(kind + '.finish', **identity, outcome='success',
                      duration_ms=round((time.perf_counter() - started) * 1000, 2))
            return result
        return wrapped
    return decorate
