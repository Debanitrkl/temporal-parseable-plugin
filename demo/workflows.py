"""Demo workflows and activities for the Temporal-Parseable plugin."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta

from temporalio import activity, workflow


# ---------------------------------------------------------------------------
# Activities
# ---------------------------------------------------------------------------

@activity.defn
async def greet(name: str) -> str:
    activity.logger.info("Generating greeting for %s", name)
    return f"Hello, {name}!"


@dataclass
class OrderItem:
    product: str
    quantity: int
    price: float


@activity.defn
async def validate_order(item: OrderItem) -> bool:
    activity.logger.info(
        "Validating order: %s x%d @ $%.2f",
        item.product,
        item.quantity,
        item.price,
    )
    if item.quantity <= 0 or item.price <= 0:
        activity.logger.warning("Invalid order parameters")
        return False
    return True


@activity.defn
async def process_payment(item: OrderItem) -> str:
    activity.logger.info(
        "Processing payment of $%.2f for %s",
        item.price * item.quantity,
        item.product,
    )
    # Simulate processing time
    await asyncio.sleep(0.5)
    confirmation = f"PAY-{hash(item.product) % 100000:05d}"
    activity.logger.info("Payment confirmed: %s", confirmation)
    return confirmation


# ---------------------------------------------------------------------------
# Workflows
# ---------------------------------------------------------------------------

@workflow.defn
class GreetingWorkflow:
    """Simple single-activity workflow."""

    @workflow.run
    async def run(self, name: str) -> str:
        workflow.logger.info("GreetingWorkflow started for %s", name)
        result = await workflow.execute_activity(
            greet,
            name,
            start_to_close_timeout=timedelta(seconds=10),
        )
        workflow.logger.info("GreetingWorkflow completed: %s", result)
        return result


@workflow.defn
class OrderWorkflow:
    """Multi-activity workflow: validate → pay."""

    @workflow.run
    async def run(self, item: OrderItem) -> str:
        workflow.logger.info("OrderWorkflow started for %s", item.product)

        is_valid = await workflow.execute_activity(
            validate_order,
            item,
            start_to_close_timeout=timedelta(seconds=10),
        )
        if not is_valid:
            workflow.logger.error("Order validation failed")
            return "ORDER_INVALID"

        confirmation = await workflow.execute_activity(
            process_payment,
            item,
            start_to_close_timeout=timedelta(seconds=30),
        )
        workflow.logger.info("OrderWorkflow completed: %s", confirmation)
        return confirmation
