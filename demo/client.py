"""Demo client that starts workflows to generate telemetry."""

from __future__ import annotations

import asyncio
import logging
import uuid

from temporalio.client import Client

from temporal_parseable import ParseableConfig, ParseablePlugin
from workflows import GreetingWorkflow, OrderItem, OrderWorkflow

TASK_QUEUE = "parseable-demo"


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    config = ParseableConfig()
    plugin = ParseablePlugin(config)

    client = await Client.connect(
        config.temporal_host,
        namespace=config.temporal_namespace,
        plugins=[plugin],
    )

    # --- GreetingWorkflow ---
    names = ["Alice", "Bob", "Charlie"]
    for name in names:
        wf_id = f"greeting-{name.lower()}-{uuid.uuid4().hex[:8]}"
        logger.info("Starting GreetingWorkflow: %s", wf_id)
        result = await client.execute_workflow(
            GreetingWorkflow.run,
            name,
            id=wf_id,
            task_queue=TASK_QUEUE,
        )
        logger.info("Result: %s", result)

    # --- OrderWorkflow ---
    orders = [
        OrderItem(product="Widget", quantity=5, price=9.99),
        OrderItem(product="Gadget", quantity=2, price=24.50),
        OrderItem(product="Invalid", quantity=-1, price=10.00),
    ]
    for order in orders:
        wf_id = f"order-{order.product.lower()}-{uuid.uuid4().hex[:8]}"
        logger.info("Starting OrderWorkflow: %s (%s)", wf_id, order.product)
        result = await client.execute_workflow(
            OrderWorkflow.run,
            order,
            id=wf_id,
            task_queue=TASK_QUEUE,
        )
        logger.info("Result: %s", result)

    logger.info("All demo workflows completed!")


if __name__ == "__main__":
    asyncio.run(main())
