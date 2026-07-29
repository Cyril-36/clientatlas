from __future__ import annotations

import hashlib
import math
from collections.abc import Sequence
from typing import Protocol

from clientatlas_ai.errors import SafeServiceError
from clientatlas_ai.local_models import encode_sentences


class EmbeddingProvider(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def model(self) -> str: ...

    async def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class HuggingFaceEmbeddingProvider:
    def __init__(
        self,
        *,
        model: str,
        device: str,
        dimensions: int,
        timeout_seconds: float,
    ) -> None:
        self._model = model
        self._device = device
        self._dimensions = dimensions
        self._timeout = timeout_seconds

    @property
    def name(self) -> str:
        return "huggingface"

    @property
    def model(self) -> str:
        return self._model

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            raw = await encode_sentences(
                texts,
                model=self._model,
                device=self._device,
                timeout_seconds=self._timeout,
            )
            if hasattr(raw, "tolist"):
                raw = raw.tolist()
        except (ImportError, OSError, RuntimeError, TimeoutError, ValueError) as error:
            raise SafeServiceError(
                "embedding_provider_unavailable",
                status_code=503,
            ) from error
        return _validate_embeddings(raw, len(texts), self._dimensions)


class DeterministicEmbeddingProvider:
    """Dependency-free provider for tests and synthetic seeded demonstrations."""

    def __init__(self, dimensions: int = 384) -> None:
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
