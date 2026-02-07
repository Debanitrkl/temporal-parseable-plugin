"""Temporal worker interceptor that records activity metrics via OpenTelemetry.

Emits the following OTel metrics:

Counters:
  - ``temporal.activity.started``   — activities started
  - ``temporal.activity.completed`` — activities completed successfully
  - ``temporal.activity.failed``    — activities that raised an exception

Histograms:
  - ``temporal.activity.duration``  — activity execution time (seconds)

All metrics carry ``activity_type``, ``workflow_type``, and ``task_queue``
attributes for filtering in Parseable.

Note: Workflow-level metrics are not collected here because workflow
interceptors run inside Temporal's deterministic sandbox, which restricts
non-deterministic calls like ``time.monotonic()`` and direct OTel SDK usage.
Workflow execution data is captured via traces instead.
"""

from __future__ import annotations

import time
from typing import Any

import temporalio.activity
from opentelemetry.metrics import Meter
from temporalio.worker import (
    ActivityInboundInterceptor,
    ExecuteActivityInput,
    Interceptor,
)

# Module-level meter reference, set by the plugin at init time
_meter: Meter | None = None


def set_meter(meter: Meter) -> None:
    """Set the global meter used by the metrics interceptor."""
    global _meter
    _meter = meter


class _MetricsActivityInterceptor(ActivityInboundInterceptor):
    """Records counters and duration histograms for activity executions."""

    async def execute_activity(self, input: ExecuteActivityInput) -> Any:
        if _meter is None:
            return await self.next.execute_activity(input)

        info = temporalio.activity.info()
        attrs = {
            "activity_type": info.activity_type,
            "workflow_type": info.workflow_type,
            "task_queue": info.task_queue,
            "namespace": info.workflow_namespace,
        }

        started = _meter.create_counter(
            "temporal.activity.started",
            description="Activities started",
        )
        completed = _meter.create_counter(
            "temporal.activity.completed",
            description="Activities completed successfully",
        )
        failed = _meter.create_counter(
            "temporal.activity.failed",
            description="Activities that raised an exception",
        )
        duration = _meter.create_histogram(
            "temporal.activity.duration",
            unit="s",
            description="Activity execution duration in seconds",
        )

        started.add(1, attrs)
        t0 = time.monotonic()
        try:
            result = await self.next.execute_activity(input)
            completed.add(1, attrs)
            return result
        except Exception:
            failed.add(1, attrs)
            raise
        finally:
            duration.record(time.monotonic() - t0, attrs)


class MetricsInterceptor(Interceptor):
    """Temporal worker interceptor that emits OTel metrics for activities."""

    def intercept_activity(
        self, next: ActivityInboundInterceptor
    ) -> ActivityInboundInterceptor:
        return _MetricsActivityInterceptor(next)
