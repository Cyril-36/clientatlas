from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, Request, Response
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

REQUESTS = Counter(
    "clientatlas_http_requests_total",
    "HTTP requests by bounded route, method, and status.",
    ("route", "method", "status"),
)
LATENCY = Histogram(
    "clientatlas_http_request_duration_seconds",
    "HTTP request latency by bounded route and method.",
    ("route", "method"),
)
INGESTION_FAILURES = Counter(
    "clientatlas_ingestion_failures_total",
    "Ingestion failures by safe code.",
    ("code",),
)
RETRIEVAL_CANDIDATES = Histogram(
    "clientatlas_retrieval_candidates",
    "Number of evidence candidates returned.",
    buckets=(0, 1, 2, 4, 8, 12, 20, 40),
)
GENERATION_REQUESTS = Counter(
    "clientatlas_generation_requests_total",
    "Validated generation requests by provider, model, and outcome.",
    ("provider", "model", "outcome"),
)
tracer = trace.get_tracer("clientatlas.ai")


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return str(path) if path else "unmatched"


def configure_telemetry(
    app: FastAPI,
    *,
    enabled: bool,
    otlp_endpoint: str | None,
) -> None:
    if not enabled:
        return
    if otlp_endpoint:
        provider = TracerProvider(
            resource=Resource.create({"service.name": "clientatlas-ai"})
        )
        exporter = OTLPSpanExporter(endpoint=f"{otlp_endpoint.rstrip('/')}/v1/traces")
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="health,metrics,docs,openapi.json",
    )

    @app.middleware("http")
    async def observe_request(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        started = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            route = _route_template(request)
            method = request.method
            REQUESTS.labels(route=route, method=method, status=str(status)).inc()
            LATENCY.labels(route=route, method=method).observe(
                time.perf_counter() - started
            )

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def safe_span_attributes(**values: object) -> dict[str, Any]:
    """Allow only operational scalars; callers must never pass content or tokens."""
    return {
        key: value
        for key, value in values.items()
        if isinstance(value, (str, bool, int, float))
    }
