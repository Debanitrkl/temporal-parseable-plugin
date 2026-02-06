"""Demo worker using the ParseablePlugin."""

from __future__ import annotations

import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from temporal_parseable import ParseableConfig, ParseablePlugin
from workflows import (
    GreetingWorkflow,
    OrderWorkflow,
    greet,
    process_payment,
    validate_order,
)

TASK_QUEUE = "parseable-demo"


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    config = ParseableConfig()
    plugin = ParseablePlugin(config)
    runtime = plugin.create_runtime()

    logger.info(
        "Connecting to Temporal at %s (namespace=%s)",
        config.temporal_host,
        config.temporal_namespace,
    )

    client = await Client.connect(
        config.temporal_host,
        namespace=config.temporal_namespace,
        plugins=[plugin],
        runtime=runtime,
    )

    logger.info("Starting worker on task queue: %s", TASK_QUEUE)

    async with Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[GreetingWorkflow, OrderWorkflow],
        activities=[greet, validate_order, process_payment],
        plugins=[plugin],
    ):
        logger.info("Worker running — press Ctrl+C to stop")
        await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nWorker stopped.")
