from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from uuid import UUID

from clientatlas_ai.auth import VerifiedClaims
from clientatlas_ai.embeddings import DeterministicEmbeddingProvider
from clientatlas_ai.evaluation import (
    load_dataset,
    report_json,
    retrieval_case_result,
)
from clientatlas_ai.retrieval import RetrievalService


async def run(args: argparse.Namespace) -> None:
    dataset = load_dataset(Path(args.dataset))
    claims = VerifiedClaims(
        audience="authenticated",
        expires_at=4_102_444_800,
        issuer="https://local.clientatlas.invalid/auth/v1",
        role="authenticated",
        subject=UUID(args.user),
    )
    service = RetrievalService(DeterministicEmbeddingProvider())
    results = []
    for case in dataset.cases:
        if not case.expectedSources:
            continue
        evidence = await service.retrieve(
            claims=claims,
            organization_id=UUID(args.organization),
            workspace_id=UUID(args.workspace),
            query=case.question,
            top_k=10,
        )
        results.append(
            retrieval_case_result(
                case,
                [item.source_name for item in evidence],
            )
        )
    report = report_json(
        dataset,
        results,
        configuration={
            "chunker": "word-window-700-overlap-80",
            "embedding": "sha256-token-hash-v1",
            "fusion": "rrf-k-60",
        },
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report + "\n", encoding="utf-8")
    print(output)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--organization", required=True)
    result.add_argument("--workspace", required=True)
    result.add_argument(
        "--user",
        default="00000000-0000-4000-8000-000000000001",
    )
    result.add_argument(
        "--dataset",
        default="packages/evaluation/datasets/v1/questions.json",
    )
    result.add_argument(
        "--output",
        default="packages/evaluation/reports/latest.json",
    )
    return result


if __name__ == "__main__":
    asyncio.run(run(parser().parse_args()))
