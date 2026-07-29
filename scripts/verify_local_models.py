from __future__ import annotations

import asyncio
import json
from uuid import UUID

from clientatlas_ai.embeddings import HuggingFaceEmbeddingProvider
from clientatlas_ai.generation import (
    HuggingFaceGenerationProvider,
    build_grounded_prompt,
    validate_generated_answer,
)
from clientatlas_ai.retrieval import EvidenceChunk


async def main() -> None:
    embeddings = HuggingFaceEmbeddingProvider(
        model="sentence-transformers/all-MiniLM-L6-v2",
        device="cpu",
        dimensions=384,
        timeout_seconds=180,
    )
    vector = (await embeddings.embed(["Avery owns the client launch."]))[0]

    evidence = (
        EvidenceChunk(
            chunk_id=UUID("11111111-1111-4111-8111-111111111111"),
            content="Avery owns the client launch.",
            fused_score=0.03,
            lexical_rank=1,
            locator={"page": 1},
            semantic_rank=1,
            source_id=UUID("22222222-2222-4222-8222-222222222222"),
            source_name="synthetic-brief.pdf",
            version_id=UUID("33333333-3333-4333-8333-333333333333"),
        ),
    )
    generation = HuggingFaceGenerationProvider(
        model="google/flan-t5-small",
        device=-1,
        max_input_characters=8_000,
        max_new_tokens=128,
        timeout_seconds=180,
    )
    raw = await generation.generate(
        build_grounded_prompt("Who owns the client launch?", evidence)
    )
    answer, citations = validate_generated_answer(raw, evidence)

    print(
        json.dumps(
            {
                "answerAbstained": answer.abstained,
                "citationCount": len(citations),
                "embeddingDimensions": len(vector),
                "embeddingModel": embeddings.model,
                "generationModel": generation.model,
                "providers": [embeddings.name, generation.name],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
