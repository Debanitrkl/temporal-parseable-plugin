"""Configuration for the Temporal-Parseable plugin."""

from __future__ import annotations

import base64
from typing import Dict

from pydantic_settings import BaseSettings


class ParseableConfig(BaseSettings):
    """Configuration for connecting to Parseable and Temporal.

    All fields can be overridden via environment variables with the
    ``PARSEABLE_`` prefix. For example, ``PARSEABLE_URL`` sets ``url``.
    """

    model_config = {"env_prefix": "PARSEABLE_"}

    # Parseable connection
    url: str = "http://localhost:8000"
    username: str = "admin"
    password: str = "admin"

    # Stream names in Parseable (one per signal)
    traces_stream: str = "temporal-traces"
    logs_stream: str = "temporal-logs"
    metrics_stream: str = "temporal-metrics"

    # Temporal connection
    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "default"

    # OpenTelemetry service identity
    service_name: str = "temporal-worker"

    # Signal toggles — disable individual signals if not needed
    enable_traces: bool = True
    enable_logs: bool = True
    enable_metrics: bool = True

    @property
    def auth_header(self) -> str:
        """Return the Basic-auth header value expected by Parseable."""
        token = base64.b64encode(
            f"{self.username}:{self.password}".encode()
        ).decode()
        return f"Basic {token}"

    # Parseable requires specific X-P-Log-Source values per signal type
    _LOG_SOURCE_MAP: Dict[str, str] = {
        "traces": "otel-traces",
        "logs": "otel-logs",
        "metrics": "otel-metrics",
    }

    def headers_for_signal(self, stream: str, signal: str) -> Dict[str, str]:
        """Build the HTTP headers Parseable requires for a given signal.

        Args:
            stream: The Parseable stream name (e.g. "temporal-traces").
            signal: The signal type — one of "traces", "logs", "metrics".
        """
        return {
            "Authorization": self.auth_header,
            "X-P-Stream": stream,
            "X-P-Log-Source": self._LOG_SOURCE_MAP.get(signal, f"otel-{signal}"),
        }

    @property
    def traces_endpoint(self) -> str:
        return f"{self.url}/v1/traces"

    @property
    def logs_endpoint(self) -> str:
        return f"{self.url}/v1/logs"

    @property
    def metrics_endpoint(self) -> str:
        return f"{self.url}/v1/metrics"
