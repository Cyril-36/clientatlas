from __future__ import annotations

import math

import pytest

from clientatlas_ai.embeddings import (
    DeterministicEmbeddingProvider,
    HuggingFaceEmbeddingProvider,
)
from clientatlas_ai.errors import SafeServiceError


async def test_deterministic_embeddings_are_stable_and_normalized() -> None:
    provider = DeterministicEmbeddingProvider(dimensions=32)
    first, second = await provider.embed(["alpha beta", "alpha beta"])
    assert first == second
    assert len(first) == 32
    assert math.isclose(sum(value * value for value in first), 1.0)


async def test_huggingface_embeddings_validate_local_model_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_encode(*args: object, **kwargs: object) -> list[list[float]]:
        del args, kwargs
        return [[1.0, 0.0, 0.0]]

    monkeypatch.setattr(
        "clientatlas_ai.embeddings.encode_sentences",
        fake_encode,
    )
    provider = HuggingFaceEmbeddingProvider(
        model="sentence-transformers/all-MiniLM-L6-v2",
        device="cpu",
        dimensions=3,
        timeout_seconds=1,
    )
    assert provider.name == "huggingface"
    assert provider.model == "sentence-transformers/all-MiniLM-L6-v2"
    assert await provider.embed(["launch owner"]) == [[1.0, 0.0, 0.0]]


async def test_huggingface_embeddings_reject_dimension_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_encode(*args: object, **kwargs: object) -> list[list[float]]:
        del args, kwargs
        return [[1.0, 0.0]]

    monkeypatch.setattr(
        "clientatlas_ai.embeddings.encode_sentences",
        fake_encode,
    )
    provider = HuggingFaceEmbeddingProvider(
        model="sentence-transformers/all-MiniLM-L6-v2",
        device="cpu",
        dimensions=3,
        timeout_seconds=1,
    )
    with pytest.raises(SafeServiceError, match="embedding_dimension_mismatch"):
        await provider.embed(["launch owner"])
