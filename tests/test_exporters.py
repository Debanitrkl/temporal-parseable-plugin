"""Tests for exporter factory functions."""

from __future__ import annotations

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

from temporal_parseable.config import ParseableConfig
from temporal_parseable.exporters import (
    create_log_exporter,
    create_metric_exporter,
    create_trace_exporter,
)


class TestTraceExporter:
    def test_returns_otlp_span_exporter(self, default_config: ParseableConfig) -> None:
        exporter = create_trace_exporter(default_config)
        assert isinstance(exporter, OTLPSpanExporter)

    def test_headers_contain_stream(self, default_config: ParseableConfig) -> None:
        headers = default_config.headers_for_signal(
            default_config.traces_stream, "traces"
        )
        assert headers["X-P-Stream"] == "temporal-traces"
        assert headers["X-P-Log-Source"] == "otel-traces"


class TestLogExporter:
    def test_returns_otlp_log_exporter(self, default_config: ParseableConfig) -> None:
        exporter = create_log_exporter(default_config)
        assert isinstance(exporter, OTLPLogExporter)

    def test_headers_contain_stream(self, default_config: ParseableConfig) -> None:
        headers = default_config.headers_for_signal(
            default_config.logs_stream, "logs"
        )
        assert headers["X-P-Stream"] == "temporal-logs"
        assert headers["X-P-Log-Source"] == "otel-logs"


class TestMetricExporter:
    def test_returns_otlp_metric_exporter(
        self, default_config: ParseableConfig
    ) -> None:
        exporter = create_metric_exporter(default_config)
        assert isinstance(exporter, OTLPMetricExporter)

    def test_headers_contain_stream(self, default_config: ParseableConfig) -> None:
        headers = default_config.headers_for_signal(
            default_config.metrics_stream, "metrics"
        )
        assert headers["X-P-Stream"] == "temporal-metrics"
        assert headers["X-P-Log-Source"] == "otel-metrics"
