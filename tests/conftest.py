"""Shared fixtures for temporal-parseable tests."""

from __future__ import annotations

import pytest

from temporal_parseable.config import ParseableConfig


@pytest.fixture
def default_config() -> ParseableConfig:
    """Return a ParseableConfig with all defaults."""
    return ParseableConfig()


@pytest.fixture
def custom_config(monkeypatch: pytest.MonkeyPatch) -> ParseableConfig:
    """Return a ParseableConfig driven by environment variables."""
    monkeypatch.setenv("PARSEABLE_URL", "http://parseable.example.com:9000")
    monkeypatch.setenv("PARSEABLE_USERNAME", "testuser")
    monkeypatch.setenv("PARSEABLE_PASSWORD", "testpass")
    monkeypatch.setenv("PARSEABLE_TRACES_STREAM", "my-traces")
    monkeypatch.setenv("PARSEABLE_LOGS_STREAM", "my-logs")
    monkeypatch.setenv("PARSEABLE_METRICS_STREAM", "my-metrics")
    monkeypatch.setenv("PARSEABLE_TEMPORAL_HOST", "temporal.example.com:7233")
    monkeypatch.setenv("PARSEABLE_SERVICE_NAME", "my-service")
    monkeypatch.setenv("PARSEABLE_ENABLE_METRICS", "false")
    return ParseableConfig()
