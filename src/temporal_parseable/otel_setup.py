"""Bootstrap OpenTelemetry SDK providers for traces, logs, and metrics."""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

from .config import ParseableConfig
from .exporters import (
    create_trace_exporter,
    create_log_exporter,
    create_metric_exporter,
)


def _build_resource(config: ParseableConfig) -> Resource:
    """Create an OTel Resource with the configured service name."""
    return Resource.create({SERVICE_NAME: config.service_name})


def setup_tracer_provider(config: ParseableConfig) -> TracerProvider:
    """Create and register a TracerProvider that exports to Parseable."""
    resource = _build_resource(config)
    provider = TracerProvider(resource=resource)
    exporter = create_trace_exporter(config)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return provider


def setup_logger_provider(config: ParseableConfig) -> LoggerProvider:
    """Create a LoggerProvider that exports to Parseable."""
    resource = _build_resource(config)
    exporter = create_log_exporter(config)
    provider = LoggerProvider(resource=resource)
    provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    return provider


def setup_meter_provider(config: ParseableConfig) -> MeterProvider:
    """Create a MeterProvider that exports to Parseable."""
    resource = _build_resource(config)
    exporter = create_metric_exporter(config)
    reader = PeriodicExportingMetricReader(exporter, export_interval_millis=10000)
    provider = MeterProvider(resource=resource, metric_readers=[reader])
    return provider
