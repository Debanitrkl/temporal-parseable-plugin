"""OTLP HTTP exporter factories for each telemetry signal.

Parseable's OTLP endpoints require JSON encoding (not protobuf).
We create custom exporters that use a requests Session with a
middleware adapter to convert protobuf payloads to OTLP JSON before sending.

The OTLP JSON spec requires bytes fields (trace_id, span_id, etc.) to be
lowercase hex strings, but protobuf's ``MessageToDict`` outputs base64.
We post-process the dict to fix this before serialising to JSON.
"""

from __future__ import annotations

import base64
import json
from typing import Any

import requests
from google.protobuf.json_format import MessageToDict
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
    ExportTraceServiceRequest,
)
from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import (
    ExportLogsServiceRequest,
)
from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import (
    ExportMetricsServiceRequest,
)

from .config import ParseableConfig

# Keys whose values are base64-encoded bytes that must become hex strings
# per the OTLP JSON specification.
_BYTES_KEYS = frozenset({
    "traceId", "spanId", "parentSpanId",
})


def _b64_to_hex(value: str) -> str:
    """Convert a base64-encoded string to a lowercase hex string."""
    try:
        raw = base64.b64decode(value)
        return raw.hex()
    except Exception:
        return value


def _fix_bytes_fields(obj: Any) -> Any:
    """Recursively convert base64 bytes fields to hex strings in a dict."""
    if isinstance(obj, dict):
        return {
            k: _b64_to_hex(v) if k in _BYTES_KEYS and isinstance(v, str)
            else _fix_bytes_fields(v)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_fix_bytes_fields(item) for item in obj]
    return obj


class _ProtobufToJsonAdapter(requests.adapters.HTTPAdapter):
    """Intercepts POST requests and converts protobuf bodies to OTLP JSON.

    The OTLP HTTP exporters always send protobuf-encoded bodies with
    ``Content-Type: application/x-protobuf``. Parseable only accepts JSON,
    so this adapter deserializes the protobuf and re-serializes to OTLP JSON
    with proper hex-encoded trace/span IDs.
    """

    def __init__(self, proto_class, **kwargs):
        self._proto_class = proto_class
        super().__init__(**kwargs)

    def send(self, request, *args, **kwargs):
        if (
            request.body
            and request.headers.get("Content-Type") == "application/x-protobuf"
        ):
            msg = self._proto_class()
            msg.ParseFromString(
                request.body if isinstance(request.body, bytes)
                else request.body.encode()
            )
            d = MessageToDict(msg, use_integers_for_enums=True)
            d = _fix_bytes_fields(d)
            body = json.dumps(d, ensure_ascii=False).encode("utf-8")
            request.body = body
            request.headers["Content-Type"] = "application/json"
            request.headers["Content-Length"] = str(len(body))
        return super().send(request, *args, **kwargs)


def _create_json_session(proto_class, endpoint: str) -> requests.Session:
    """Create a requests Session that converts protobuf to JSON."""
    session = requests.Session()
    session.mount(endpoint, _ProtobufToJsonAdapter(proto_class))
    return session


def create_trace_exporter(config: ParseableConfig) -> OTLPSpanExporter:
    """Create an OTLP HTTP span exporter targeting the Parseable traces stream."""
    session = _create_json_session(
        ExportTraceServiceRequest, config.traces_endpoint
    )
    return OTLPSpanExporter(
        endpoint=config.traces_endpoint,
        headers=config.headers_for_signal(config.traces_stream, "traces"),
        session=session,
    )


def create_log_exporter(config: ParseableConfig) -> OTLPLogExporter:
    """Create an OTLP HTTP log exporter targeting the Parseable logs stream."""
    session = _create_json_session(
        ExportLogsServiceRequest, config.logs_endpoint
    )
    return OTLPLogExporter(
        endpoint=config.logs_endpoint,
        headers=config.headers_for_signal(config.logs_stream, "logs"),
        session=session,
    )


def create_metric_exporter(config: ParseableConfig) -> OTLPMetricExporter:
    """Create an OTLP HTTP metric exporter targeting the Parseable metrics stream."""
    session = _create_json_session(
        ExportMetricsServiceRequest, config.metrics_endpoint
    )
    return OTLPMetricExporter(
        endpoint=config.metrics_endpoint,
        headers=config.headers_for_signal(config.metrics_stream, "metrics"),
        session=session,
    )
