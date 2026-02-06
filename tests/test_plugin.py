"""Tests for ParseablePlugin initialization and wiring."""

from __future__ import annotations

from temporal_parseable.config import ParseableConfig
from temporal_parseable.plugin import ParseablePlugin


class TestPluginInit:
    def test_creates_with_defaults(self) -> None:
        plugin = ParseablePlugin()
        assert plugin.config.url == "http://localhost:8000"

    def test_creates_with_custom_config(self) -> None:
        config = ParseableConfig(url="http://custom:9000", service_name="test-svc")
        plugin = ParseablePlugin(config)
        assert plugin.config.url == "http://custom:9000"
        assert plugin.config.service_name == "test-svc"

    def test_providers_created_when_all_enabled(self) -> None:
        plugin = ParseablePlugin()
        # tracer + logger + meter = 3 providers
        assert len(plugin._providers) == 3

    def test_no_providers_when_all_disabled(self) -> None:
        config = ParseableConfig(
            enable_traces=False,
            enable_logs=False,
            enable_metrics=False,
        )
        plugin = ParseablePlugin(config)
        assert len(plugin._providers) == 0

    def test_traces_only(self) -> None:
        config = ParseableConfig(
            enable_traces=True,
            enable_logs=False,
            enable_metrics=False,
        )
        plugin = ParseablePlugin(config)
        assert len(plugin._providers) == 1

    def test_plugin_name(self) -> None:
        plugin = ParseablePlugin()
        assert plugin.name() == "temporal-parseable"


class TestCreateRuntime:
    def test_returns_runtime_with_metrics(self) -> None:
        plugin = ParseablePlugin()
        runtime = plugin.create_runtime()
        assert runtime is not None

    def test_returns_default_runtime_when_metrics_disabled(self) -> None:
        config = ParseableConfig(enable_metrics=False)
        plugin = ParseablePlugin(config)
        runtime = plugin.create_runtime()
        # Should return the default runtime
        assert runtime is not None
