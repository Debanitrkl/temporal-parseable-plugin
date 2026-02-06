"""Tests for ParseableConfig."""

from __future__ import annotations

import base64

from temporal_parseable.config import ParseableConfig


class TestDefaults:
    def test_default_url(self, default_config: ParseableConfig) -> None:
        assert default_config.url == "http://localhost:8000"

    def test_default_credentials(self, default_config: ParseableConfig) -> None:
        assert default_config.username == "admin"
        assert default_config.password == "admin"

    def test_default_streams(self, default_config: ParseableConfig) -> None:
        assert default_config.traces_stream == "temporal-traces"
        assert default_config.logs_stream == "temporal-logs"
        assert default_config.metrics_stream == "temporal-metrics"

    def test_default_temporal_host(self, default_config: ParseableConfig) -> None:
        assert default_config.temporal_host == "localhost:7233"

    def test_default_service_name(self, default_config: ParseableConfig) -> None:
        assert default_config.service_name == "temporal-worker"

    def test_all_signals_enabled(self, default_config: ParseableConfig) -> None:
        assert default_config.enable_traces is True
        assert default_config.enable_logs is True
        assert default_config.enable_metrics is True


class TestEnvOverrides:
    def test_url_override(self, custom_config: ParseableConfig) -> None:
        assert custom_config.url == "http://parseable.example.com:9000"

    def test_credentials_override(self, custom_config: ParseableConfig) -> None:
        assert custom_config.username == "testuser"
        assert custom_config.password == "testpass"

    def test_stream_override(self, custom_config: ParseableConfig) -> None:
        assert custom_config.traces_stream == "my-traces"
        assert custom_config.logs_stream == "my-logs"
        assert custom_config.metrics_stream == "my-metrics"

    def test_temporal_host_override(self, custom_config: ParseableConfig) -> None:
        assert custom_config.temporal_host == "temporal.example.com:7233"

    def test_service_name_override(self, custom_config: ParseableConfig) -> None:
        assert custom_config.service_name == "my-service"

    def test_signal_toggle(self, custom_config: ParseableConfig) -> None:
        assert custom_config.enable_metrics is False


class TestAuthHeader:
    def test_auth_header_format(self, default_config: ParseableConfig) -> None:
        header = default_config.auth_header
        assert header.startswith("Basic ")

    def test_auth_header_encoding(self, default_config: ParseableConfig) -> None:
        header = default_config.auth_header
        encoded = header.removeprefix("Basic ")
        decoded = base64.b64decode(encoded).decode()
        assert decoded == "admin:admin"

    def test_auth_header_custom_creds(self, custom_config: ParseableConfig) -> None:
        header = custom_config.auth_header
        encoded = header.removeprefix("Basic ")
        decoded = base64.b64decode(encoded).decode()
        assert decoded == "testuser:testpass"


class TestHeadersForSignal:
    def test_contains_required_keys(self, default_config: ParseableConfig) -> None:
        headers = default_config.headers_for_signal("my-stream", "traces")
        assert "Authorization" in headers
        assert "X-P-Stream" in headers
        assert "X-P-Log-Source" in headers

    def test_stream_name(self, default_config: ParseableConfig) -> None:
        headers = default_config.headers_for_signal("test-stream", "traces")
        assert headers["X-P-Stream"] == "test-stream"

    def test_log_source_traces(self, default_config: ParseableConfig) -> None:
        headers = default_config.headers_for_signal("s", "traces")
        assert headers["X-P-Log-Source"] == "otel-traces"

    def test_log_source_logs(self, default_config: ParseableConfig) -> None:
        headers = default_config.headers_for_signal("s", "logs")
        assert headers["X-P-Log-Source"] == "otel-logs"

    def test_log_source_metrics(self, default_config: ParseableConfig) -> None:
        headers = default_config.headers_for_signal("s", "metrics")
        assert headers["X-P-Log-Source"] == "otel-metrics"


class TestEndpoints:
    def test_traces_endpoint(self, default_config: ParseableConfig) -> None:
        assert default_config.traces_endpoint == "http://localhost:8000/v1/traces"

    def test_logs_endpoint(self, default_config: ParseableConfig) -> None:
        assert default_config.logs_endpoint == "http://localhost:8000/v1/logs"

    def test_metrics_endpoint(self, default_config: ParseableConfig) -> None:
        assert default_config.metrics_endpoint == "http://localhost:8000/v1/metrics"

    def test_custom_url_endpoints(self, custom_config: ParseableConfig) -> None:
        assert custom_config.traces_endpoint == (
            "http://parseable.example.com:9000/v1/traces"
        )
