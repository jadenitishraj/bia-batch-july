"""App-process CPU/peak RSS and HTTP counters, sent directly with remote_write."""
import os
import resource
import sys

from opentelemetry.exporter.prometheus_remote_write import (
    PrometheusRemoteWriteMetricsExporter,
)
from opentelemetry.metrics import Observation
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource


def process_cpu(_):
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return [Observation(usage.ru_utime + usage.ru_stime, {'app': 'travel-planner'})]


def process_memory(_):
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return [Observation(peak * (1 if sys.platform == 'darwin' else 1024), {'app': 'travel-planner'})]


def configure_metrics():
    readers = []
    if all(os.getenv(key) for key in ('GRAFANA_PROMETHEUS_URL', 'GRAFANA_PROMETHEUS_USER', 'GRAFANA_CLOUD_TOKEN')):
        exporter = PrometheusRemoteWriteMetricsExporter(
            endpoint=os.environ['GRAFANA_PROMETHEUS_URL'], timeout=5,
            basic_auth={'username': os.environ['GRAFANA_PROMETHEUS_USER'],
                        'password': os.environ['GRAFANA_CLOUD_TOKEN']},
        )
        readers.append(PeriodicExportingMetricReader(exporter, export_interval_millis=10000))
    provider = MeterProvider(resource=Resource.create({'service.name': 'travel-planner'}),
                             metric_readers=readers)
    meter = provider.get_meter('travel-planner')
    meter.create_observable_counter('travel_planner_process_cpu_seconds', [process_cpu], unit='s',
                                    description='Cumulative CPU time used by this app process.')
    meter.create_observable_gauge('travel_planner_process_peak_resident_memory_bytes', [process_memory],
                                  unit='By', description='Peak resident memory of this app process.')
    requests = meter.create_counter('travel_planner_http_requests',
                                     description='Completed HTTP requests, including streamed responses.')
    return provider, requests
