"""Bridge Python logging to the OpenTelemetry LoggerProvider.

Temporal's ``workflow.logger`` and ``activity.logger`` emit standard
Python ``logging`` records.  This module re-exports the SDK's built-in
``LoggingHandler`` which converts them into OTel ``LogRecord`` objects
so they are exported via the OTLP pipeline.
"""

from __future__ import annotations

from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler


def create_otel_logging_handler(logger_provider: LoggerProvider) -> LoggingHandler:
    """Create a logging.Handler that forwards records to an OTel LoggerProvider.

    This registers the provider globally and returns a handler that can be
    attached to any Python logger (e.g. the root logger).
    """
    set_logger_provider(logger_provider)
    return LoggingHandler(logger_provider=logger_provider)
