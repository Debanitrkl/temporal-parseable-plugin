"""ParseablePlugin — Temporal SimplePlugin that exports telemetry to Parseable."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from temporalio.contrib.opentelemetry import TracingInterceptor
from temporalio.plugin import SimplePlugin
from temporalio.runtime import OpenTelemetryConfig, Runtime, TelemetryConfig

from .config import ParseableConfig
from .logging_handler import create_otel_logging_handler
from .metrics_interceptor import MetricsInterceptor, set_meter
from .otel_setup import (
    setup_logger_provider,
    setup_meter_provider,
    setup_tracer_provider,
)

logger = logging.getLogger(__name__)


class ParseablePlugin(SimplePlugin):
    """A Temporal plugin that exports traces, logs, and metrics to Parseable.

    Usage::

        config = ParseableConfig()
        plugin = ParseablePlugin(config)

        client = await Client.connect(
            config.temporal_host,
            plugins=[plugin],
            runtime=plugin.create_runtime(),
        )

        worker = Worker(
            client,
            task_queue="my-queue",
            workflows=[...],
            activities=[...],
            plugins=[plugin],
        )
    """

    def __init__(self, config: ParseableConfig | None = None) -> None:
        self.config = config or ParseableConfig()
        self._providers: list = []

        # --- Tracing ---
        tracing_interceptor = None
        if self.config.enable_traces:
            tracer_provider = setup_tracer_provider(self.config)
            self._providers.append(tracer_provider)
            tracing_interceptor = TracingInterceptor()
            logger.info("Traces enabled → %s", self.config.traces_stream)

        # --- Logging ---
        if self.config.enable_logs:
            logger_provider = setup_logger_provider(self.config)
            self._providers.append(logger_provider)
            handler = create_otel_logging_handler(logger_provider)
            handler.setLevel(logging.DEBUG)
            logging.getLogger().addHandler(handler)
            logger.info("Logs enabled → %s", self.config.logs_stream)

        # --- Metrics ---
        metrics_interceptor = None
        if self.config.enable_metrics:
            meter_provider = setup_meter_provider(self.config)
            self._providers.append(meter_provider)
            meter = meter_provider.get_meter("temporal-parseable")
            set_meter(meter)
            metrics_interceptor = MetricsInterceptor()
            logger.info("Metrics enabled → %s", self.config.metrics_stream)

        # Build interceptor lists for SimplePlugin
        client_interceptors = [tracing_interceptor] if tracing_interceptor else []
        worker_interceptors = [metrics_interceptor] if metrics_interceptor else []

        super().__init__(
            name="temporal-parseable",
            client_interceptors=client_interceptors or None,
            worker_interceptors=worker_interceptors or None,
            run_context=self._run_context,
        )

    def create_runtime(self) -> Runtime:
        """Create a Temporal Runtime with SDK-level metrics exported to Parseable.

        Pass the returned runtime to ``Client.connect(..., runtime=runtime)``
        so that internal Temporal SDK metrics (e.g. long-poll latency,
        task-slot utilization) are also forwarded.
        """
        if not self.config.enable_metrics:
            return Runtime.default()

        return Runtime(
            telemetry=TelemetryConfig(
                metrics=OpenTelemetryConfig(
                    url=self.config.metrics_endpoint,
                    headers=self.config.headers_for_signal(
                        self.config.metrics_stream, "metrics"
                    ),
                    http=True,
                ),
                global_tags={"service.name": self.config.service_name},
            )
        )

    @asynccontextmanager
    async def _run_context(self) -> AsyncIterator[None]:
        """Async context manager that shuts down all OTel providers on exit."""
        logger.info("ParseablePlugin: starting telemetry pipeline")
        try:
            yield
        finally:
            logger.info("ParseablePlugin: shutting down telemetry pipeline")
            for provider in self._providers:
                try:
                    provider.shutdown()
                except Exception:
                    logger.exception(
                        "Error shutting down provider %s", type(provider).__name__
                    )
