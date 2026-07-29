from __future__ import annotations

from uuid import uuid4

import pytest

from clientatlas_ai.artifacts import (
    HuggingFaceArtifactProvider,
    evidence_pointers,
    validate_artifact_content,
)
from clientatlas_ai.errors import SafeServiceError
from clientatlas_ai.generation import build_grounded_prompt
from clientatlas_ai.retrieval import EvidenceChunk


def chunk() -> EvidenceChunk:
    return EvidenceChunk(
        chunk_id=uuid4(),
        content="The launch owner is Avery.",
        fused_score=0.02,
        lexical_rank=1,
        locator={"page": 1},
        semantic_rank=1,
        source_id=uuid4(),
        source_name="brief.pdf",
        version_id=uuid4(),
    )


def test_validates_artifact_and_extracts_json_pointer() -> None:
    evidence = chunk()
    content = validate_artifact_content(
        {
            "artifact_type": "onboarding_brief",
            "objectives": [],
            "open_questions": [],
            "risks": [],
            "stakeholders": [],
            "summary": [
                {
                    "evidence_ids": [str(evidence.chunk_id)],
                    "text": "Avery owns launch.",
                }
            ],
        },
        artifact_type="onboarding_brief",
        allowed_evidence={evidence.chunk_id: evidence},
    )
    assert evidence_pointers(content) == (
        ("/summary/0/evidence_ids/0", evidence.chunk_id),
    )


def test_rejects_artifact_with_invented_evidence() -> None:
    evidence = chunk()
    with pytest.raises(SafeServiceError, match="invented_artifact_evidence"):
        validate_artifact_content(
            {
                "artifact_type": "readiness_report",
                "contradictions": [],
                "follow_up_questions": [],
                "missing_information": [],
                "readiness_score": 80,
                "risks": [],
                "supported_facts": [
                    {
                        "evidence_ids": [str(uuid4())],
                        "text": "Unsupported",
                    }
                ],
            },
            artifact_type="readiness_report",
            allowed_evidence={evidence.chunk_id: evidence},
        )


async def test_huggingface_artifact_provider_wraps_allowed_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_generate(*args: object, **kwargs: object) -> str:
        del args, kwargs
        return "Avery owns the launch plan."

    monkeypatch.setattr(
        "clientatlas_ai.artifacts.generate_text",
        fake_generate,
    )
    evidence = chunk()
    provider = HuggingFaceArtifactProvider(
        model="google/flan-t5-small",
        device=-1,
        max_input_characters=8_000,
        max_new_tokens=128,
        timeout_seconds=1,
    )
    raw = await provider.generate(
        build_grounded_prompt("Generate an onboarding brief.", (evidence,)),
        {},
        "onboarding_brief",
        (evidence,),
    )
    content = validate_artifact_content(
        raw,
        artifact_type="onboarding_brief",
        allowed_evidence={evidence.chunk_id: evidence},
    )
    assert content.summary[0].text == "Avery owns the launch plan."
    assert content.summary[0].evidence_ids == [evidence.chunk_id]
