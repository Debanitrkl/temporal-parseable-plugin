# Temporal-Parseable Plugin

A [Temporal](https://temporal.io) plugin that exports OpenTelemetry traces, logs, and metrics directly to [Parseable](https://parseable.com) — no intermediate OTel Collector required.

## Architecture

```
┌──────────────┐    OTLP/HTTP     ┌──────────────┐
│   Temporal   │ ──────────────── │   Parseable  │
│   Worker     │  traces / logs   │              │
│  + Plugin    │  / metrics       │  temporal-*  │
└──────────────┘                  └──────────────┘
```

The plugin uses `SimplePlugin` from the Temporal SDK and `TracingInterceptor` from `temporalio.contrib.opentelemetry` to capture distributed traces across workflow and activity boundaries. Python `logging` calls from workflows and activities are bridged to OTel log records.

## Quick Start

### 1. Install

```bash
pip install -e .
```

### 2. Start Infrastructure

```bash
cd docker
docker compose up -d
```

This starts Parseable (`:8000`) and Temporal (`:7233`).

### 3. Run the Demo

```bash
# Terminal 1 — worker
cd demo
python worker.py

# Terminal 2 — client
cd demo
python client.py
```

### 4. Verify in Parseable

Open [http://localhost:8000](http://localhost:8000) (admin/admin) and check the streams:

```sql
SELECT trace_id, span_id, service_name, operation_name
FROM "temporal-traces" ORDER BY p_timestamp DESC LIMIT 20;

SELECT p_timestamp, severity_text, body, service_name
FROM "temporal-logs" ORDER BY p_timestamp DESC LIMIT 20;

SELECT * FROM "temporal-metrics" LIMIT 20;
```

## Usage

```python
from temporalio.client import Client
from temporalio.worker import Worker
from temporal_parseable import ParseablePlugin, ParseableConfig

config = ParseableConfig()
plugin = ParseablePlugin(config)
runtime = plugin.create_runtime()

client = await Client.connect(
    config.temporal_host,
    plugins=[plugin],
    runtime=runtime,
)

async with Worker(
    client,
    task_queue="my-queue",
    workflows=[MyWorkflow],
    activities=[my_activity],
    plugins=[plugin],
):
    await asyncio.Event().wait()
```

## Configuration

All settings are configurable via environment variables with the `PARSEABLE_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `PARSEABLE_URL` | `http://localhost:8000` | Parseable server URL |
| `PARSEABLE_USERNAME` | `admin` | Parseable username |
| `PARSEABLE_PASSWORD` | `admin` | Parseable password |
| `PARSEABLE_TRACES_STREAM` | `temporal-traces` | Stream name for trace data |
| `PARSEABLE_LOGS_STREAM` | `temporal-logs` | Stream name for log data |
| `PARSEABLE_METRICS_STREAM` | `temporal-metrics` | Stream name for metric data |
| `PARSEABLE_TEMPORAL_HOST` | `localhost:7233` | Temporal server address |
| `PARSEABLE_TEMPORAL_NAMESPACE` | `default` | Temporal namespace |
| `PARSEABLE_SERVICE_NAME` | `temporal-worker` | OTel service name |
| `PARSEABLE_ENABLE_TRACES` | `true` | Enable trace export |
| `PARSEABLE_ENABLE_LOGS` | `true` | Enable log export |
| `PARSEABLE_ENABLE_METRICS` | `true` | Enable metric export |

Copy `.env.example` and modify as needed:

```bash
cp .env.example .env
```

## Collector Mode

For environments that already run an OTel Collector:

```bash
cd docker
docker compose -f docker-compose.yaml -f docker-compose.collector.yaml up -d
```

Then point your worker at the collector instead of Parseable directly:

```bash
export PARSEABLE_URL=http://localhost:4318
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
