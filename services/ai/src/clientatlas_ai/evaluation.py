from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CaseCategory = Literal["answerable", "unanswerable", "contradictory", "injection"]


class EvaluationCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^q[0-9]{3}$")
    category: CaseCategory
    question: str
    answerable: bool
    expectedSources: list[str]
    requiredTerms: list[str]


class EvaluationDataset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    datasetVersion: str
    corpus: str
    cases: list[EvaluationCase] = Field(min_length=30, max_length=50)


@dataclass(frozen=True, slots=True)
class CaseResult:
    case_id: str
    retrieved_sources: tuple[str, ...]
    recall_at_k: float
    reciprocal_rank: float
    ndcg: float


def load_dataset(path: Path) -> EvaluationDataset:
    return EvaluationDataset.model_validate_json(path.read_text(encoding="utf-8"))


def retrieval_case_result(
    case: EvaluationCase,
    retrieved_sources: list[str],
) -> CaseResult:
    expected = set(case.expectedSources)
    # This is a document-level metric. Multiple chunks from one source count once.
    ordered = tuple(dict.fromkeys(retrieved_sources))
    if not expected:
        return CaseResult(
            case_id=case.id,
            retrieved_sources=ordered,
            recall_at_k=1.0,
            reciprocal_rank=1.0,
            ndcg=1.0,
        )
    found = expected.intersection(ordered)
    recall = len(found) / len(expected)
    first_rank = next(
        (index for index, source in enumerate(ordered, start=1) if source in expected),
        None,
    )
    reciprocal_rank = 0.0 if first_rank is None else 1.0 / first_rank
    gains = [1.0 if source in expected else 0.0 for source in ordered]
    dcg = sum(gain / math.log2(index + 1) for index, gain in enumerate(gains, 1))
    ideal_length = min(len(expected), len(ordered))
    ideal = sum(1.0 / math.log2(index + 1) for index in range(1, ideal_length + 1))
    ndcg = dcg / ideal if ideal else 0.0
    return CaseResult(
        case_id=case.id,
        retrieved_sources=ordered,
        recall_at_k=recall,
        reciprocal_rank=reciprocal_rank,
        ndcg=ndcg,
    )


def citation_precision(cited_ids: list[str], allowed_ids: set[str]) -> float:
    if not cited_ids:
        return 1.0
    return sum(item in allowed_ids for item in cited_ids) / len(cited_ids)


def abstention_accuracy(
    expected_answerable: list[bool],
    actual_abstained: list[bool],
) -> float:
    if len(expected_answerable) != len(actual_abstained) or not expected_answerable:
        raise ValueError("aligned non-empty evaluation arrays are required")
    correct = sum(
        answerable is not abstained
        for answerable, abstained in zip(
            expected_answerable,
            actual_abstained,
            strict=True,
        )
    )
    return correct / len(expected_answerable)


def summarize_retrieval(results: list[CaseResult]) -> dict[str, float | int]:
    if not results:
        raise ValueError("at least one result is required")
    count = len(results)
    return {
        "caseCount": count,
        "meanRecallAtK": sum(item.recall_at_k for item in results) / count,
        "mrr": sum(item.reciprocal_rank for item in results) / count,
        "meanNdcg": sum(item.ndcg for item in results) / count,
    }


def report_json(
    dataset: EvaluationDataset,
    results: list[CaseResult],
    *,
    configuration: dict[str, str],
) -> str:
    return json.dumps(
        {
            "configuration": configuration,
            "datasetVersion": dataset.datasetVersion,
            "metrics": summarize_retrieval(results),
            "results": [
                {
                    "caseId": item.case_id,
                    "ndcg": item.ndcg,
                    "recallAtK": item.recall_at_k,
                    "reciprocalRank": item.reciprocal_rank,
                    "retrievedSources": item.retrieved_sources,
                }
                for item in results
            ],
        },
        indent=2,
        sort_keys=True,
    )
