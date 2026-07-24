from __future__ import annotations

import math

from clientatlas_ai.embeddings import DeterministicEmbeddingProvider


async def test_deterministic_embeddings_are_stable_and_normalized() -> None:
    provider = DeterministicEmbeddingProvider(dimensions=32)
    first, second = await provider.embed(["alpha beta", "alpha beta"])
    assert first == second
    assert len(first) == 32
    assert math.isclose(sum(value * value for value in first), 1.0)
