from __future__ import annotations

from pathlib import Path

from clientatlas_ai.evaluation import (
    abstention_accuracy,
    citation_precision,
    load_dataset,
    retrieval_case_result,
    summarize_retrieval,
)

DATASET = (
    Path(__file__).parents[3]
    / "packages"
    / "evaluation"
    / "datasets"
    / "v1"
    / "questions.json"
)


def test_frozen_dataset_has_required_coverage() -> None:
    dataset = load_dataset(DATASET)
    assert len(dataset.cases) == 30
    assert {case.category for case in dataset.cases} == {
        "answerable",
        "contradictory",
        "injection",
        "unanswerable",
    }
    assert len({case.id for case in dataset.cases}) == 30


def test_retrieval_metrics_reward_expected_source_order() -> None:
    case = load_dataset(DATASET).cases[0]
    result = retrieval_case_result(
        case,
        ["irrelevant.docx", "irrelevant.docx", "northstar-brief.docx"],
    )
    assert result.recall_at_k == 1.0
    assert result.reciprocal_rank == 0.5
    assert result.retrieved_sources == (
        "irrelevant.docx",
        "northstar-brief.docx",
    )
    assert 0 < result.ndcg < 1
    summary = summarize_retrieval([result])
    assert summary["caseCount"] == 1


def test_citation_and_abstention_metrics() -> None:
    assert citation_precision(["a", "bad"], {"a", "b"}) == 0.5
    assert abstention_accuracy([True, False], [False, True]) == 1.0
