from __future__ import annotations

from clientatlas_ai.retrieval import vector_literal
from clientatlas_ai.routes_retrieval import RetrievalRequest


def test_vector_literal_is_fixed_numeric_data() -> None:
    assert vector_literal([0.5, -0.25, 0.0]) == "[0.5,-0.25,0]"


def test_retrieval_request_is_bounded_and_forbids_extra_fields() -> None:
    request = RetrievalRequest.model_validate({"query": "launch owner", "top_k": 5})
    assert request.top_k == 5

    try:
        RetrievalRequest.model_validate(
            {"query": "launch", "top_k": 500, "sql": "drop table"}
        )
    except ValueError:
        pass
    else:
        raise AssertionError("invalid retrieval request was accepted")
