"""One shared logger. Log fixed event messages, never prompts, results or keys."""
import logging
import os
from queue import Queue

from logging_loki import LokiQueueHandler

logger = logging.getLogger('travel-planner')
logger.setLevel(logging.INFO)
logger.propagate = False
logger.addHandler(logging.StreamHandler())
if all(os.getenv(key) for key in ('GRAFANA_LOKI_URL', 'GRAFANA_LOKI_USER', 'GRAFANA_CLOUD_TOKEN')):
    logger.addHandler(LokiQueueHandler(Queue(), url=os.environ['GRAFANA_LOKI_URL'], version='1',
        tags={'app': 'travel-planner'}, auth=(os.environ['GRAFANA_LOKI_USER'], os.environ['GRAFANA_CLOUD_TOKEN'])))
for handler in logger.handlers:
    handler.setFormatter(logging.Formatter('{"level": "%(levelname)s", "event": "%(message)s"}'))
