from __future__ import annotations

import hashlib
import math
from collections.abc import Sequence
from typing import Protocol

import httpx

from clientatlas_ai.errors import SafeServiceError


class EmbeddingProvider(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def model(self) -> str: ...

    async def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class OllamaEmbeddingProvider:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        dimensions: int,
        timeout_seconds: float,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._dimensions = dimensions
        self._timeout = timeout_seconds

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def model(self) -> str:
        return self._model

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/api/embed",
                    json={"input": list(texts), "model": self._model},
                )
                response.raise_for_status()
                raw = response.json().get("embeddings")
        except (httpx.HTTPError, ValueError) as error:
            raise SafeServiceError(
                "embedding_provider_unavailable",
                status_code=503,
            ) from error
        return _validate_embeddings(raw, len(texts), self._dimensions)


class DeterministicEmbeddingProvider:
    """Dependency-free provider for tests and synthetic seeded demonstrations."""

    def __init__(self, dimensions: int = 768) -> None:
        self._dimensions = dimensions

    @property
    def name(self) -> str:
        return "deterministic"

    @property
    def model(self) -> str:
        return "sha256-token-hash-v1"

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vector = [0.0] * self._dimensions
            for token in text.lower().split():
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                bucket = int.from_bytes(digest[:4], "big") % self._dimensions
                sign = 1.0 if digest[4] & 1 else -1.0
                vector[bucket] += sign
            norm = math.sqrt(sum(value * value for value in vector)) or 1.0
            vectors.append([value / norm for value in vector])
        return vectors


def _validate_embeddings(
    raw: object,
    expected_count: int,
    dimensions: int,
) -> list[list[float]]:
    if not isinstance(raw, list) or len(raw) != expected_count:
        raise SafeServiceError("invalid_embedding_response", status_code=502)
    result: list[list[float]] = []
    for candidate in raw:
        if not isinstance(candidate, list) or len(candidate) != dimensions:
            raise SafeServiceError("embedding_dimension_mismatch", status_code=502)
        vector = [float(value) for value in candidate]
        if not all(math.isfinite(value) for value in vector):
            raise SafeServiceError("invalid_embedding_response", status_code=502)
        result.append(vector)
    return result
