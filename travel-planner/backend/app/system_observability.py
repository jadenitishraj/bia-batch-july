"""Start telemetry with the app; observe HTTP completion without buffering streams."""
import time
from contextlib import asynccontextmanager

from .event_log import configure_logging, log_event
from .process_metrics import configure_metrics


@asynccontextmanager
async def lifespan(app):
    listener = configure_logging()
    provider, app.state.request_count = configure_metrics()
    log_event('app.start', outcome='success')
    try:
        yield
    finally:
        provider.shutdown()
        log_event('app.stop', outcome='success')
        listener.stop()


class RequestObserver:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        started, status = time.perf_counter(), 500

        async def forward(message):
            nonlocal status
            if message['type'] == 'http.response.start':
                status = message['status']
            await send(message)

        try:
            await self.app(scope, receive, forward)
        finally:
            route = getattr(scope.get('route'), 'path', 'unmatched')
            attributes = {'app': 'travel-planner', 'method': scope['method'],
                          'route': route, 'status_code': str(status)}
            counter = getattr(scope['app'].state, 'request_count', None)
            if counter:
                counter.add(1, attributes)
            log_event('request.finish', method=scope['method'], route=route, status_code=status,
                      duration_ms=round((time.perf_counter() - started) * 1000, 2))
