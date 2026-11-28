"""Packages collect API and app-process metrics; export directly to Grafana Cloud."""
import os

from opentelemetry.exporter.prometheus_remote_write import (
    PrometheusRemoteWriteMetricsExporter,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource


def setup_metrics(app):
    if not all(os.getenv(key) for key in ('GRAFANA_PROMETHEUS_URL', 'GRAFANA_PROMETHEUS_USER', 'GRAFANA_CLOUD_TOKEN')):
        return
    exporter = PrometheusRemoteWriteMetricsExporter(endpoint=os.environ['GRAFANA_PROMETHEUS_URL'], timeout=5,
        basic_auth={'username': os.environ['GRAFANA_PROMETHEUS_USER'], 'password': os.environ['GRAFANA_CLOUD_TOKEN']})
    provider = MeterProvider(resource=Resource.create({'service.name': 'travel-planner', 'app': 'travel-planner'}),
        metric_readers=[PeriodicExportingMetricReader(exporter, export_interval_millis=10000)])
    SystemMetricsInstrumentor(config={'process.cpu.time': ['user', 'system'], 'process.memory.usage': None}).instrument(meter_provider=provider)
    FastAPIInstrumentor.instrument_app(app, meter_provider=provider)
