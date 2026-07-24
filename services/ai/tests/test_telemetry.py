from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from clientatlas_ai.main import app
from clientatlas_ai.telemetry import safe_span_attributes


async def test_metrics_expose_bounded_route_without_request_content() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/health")
        response = await client.get("/metrics")
    assert response.status_code == 200
    assert 'route="/health"' in response.text
    assert "authorization" not in response.text.lower()


def test_safe_span_attributes_drop_structured_payloads() -> None:
    assert safe_span_attributes(
        candidate_count=8,
        document_body={"secret": "text"},
        provider="ollama",
        token=["secret"],
    ) == {"candidate_count": 8, "provider": "ollama"}
