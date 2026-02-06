"""E2E test: run demo workflows in Temporal's test environment."""

from __future__ import annotations

import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

import sys
import os

# Add demo directory to path so we can import workflows
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "demo"))

from workflows import (  # noqa: E402
    GreetingWorkflow,
    OrderItem,
    OrderWorkflow,
    greet,
    process_payment,
    validate_order,
)

TASK_QUEUE = "test-queue"


@pytest.fixture
async def env():
    async with await WorkflowEnvironment.start_time_skipping() as env:
        yield env


@pytest.fixture
async def worker(env: WorkflowEnvironment):
    async with Worker(
        env.client,
        task_queue=TASK_QUEUE,
        workflows=[GreetingWorkflow, OrderWorkflow],
        activities=[greet, validate_order, process_payment],
    ) as w:
        yield w


class TestGreetingWorkflow:
    async def test_greeting(self, env: WorkflowEnvironment, worker: Worker) -> None:
        result = await env.client.execute_workflow(
            GreetingWorkflow.run,
            "World",
            id="test-greeting",
            task_queue=TASK_QUEUE,
        )
        assert result == "Hello, World!"


class TestOrderWorkflow:
    async def test_valid_order(self, env: WorkflowEnvironment, worker: Worker) -> None:
        item = OrderItem(product="Widget", quantity=3, price=9.99)
        result = await env.client.execute_workflow(
            OrderWorkflow.run,
            item,
            id="test-order-valid",
            task_queue=TASK_QUEUE,
        )
        assert result.startswith("PAY-")

    async def test_invalid_order(
        self, env: WorkflowEnvironment, worker: Worker
    ) -> None:
        item = OrderItem(product="Bad", quantity=-1, price=5.00)
        result = await env.client.execute_workflow(
            OrderWorkflow.run,
            item,
            id="test-order-invalid",
            task_queue=TASK_QUEUE,
        )
        assert result == "ORDER_INVALID"
