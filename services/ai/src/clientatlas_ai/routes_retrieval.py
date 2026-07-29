from __future__ import annotations

from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from clientatlas_ai.auth import VerifiedClaims, require_verified_claims
from clientatlas_ai.embeddings import (
    DeterministicEmbeddingProvider,
    HuggingFaceEmbeddingProvider,
)
from clientatlas_ai.retrieval import RetrievalService
from clientatlas_ai.settings import get_settings

router = APIRouter(
    prefix="/v1/organizations/{organization_id}/workspaces/{workspace_id}",
    tags=["retrieval"],
)


class RetrievalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=2_000)
    top_k: int = Field(default=8, ge=1, le=20)


@lru_cache
def get_retrieval_service() -> RetrievalService:
    settings = get_settings()
    provider = (
        DeterministicEmbeddingProvider(settings.embedding_dimensions)
        if settings.environment == "test"
        else HuggingFaceEmbeddingProvider(
            model=settings.huggingface_embedding_model,
            device=settings.huggingface_embedding_device,
            dimensions=settings.embedding_dimensions,
            timeout_seconds=settings.llm_timeout_seconds,
        )
    )
    return RetrievalService(provider)


@router.post("/retrieve")
async def retrieve(
    organization_id: UUID,
    workspace_id: UUID,
    request: RetrievalRequest,
    claims: Annotated[VerifiedClaims, Depends(require_verified_claims)],
    service: Annotated[RetrievalService, Depends(get_retrieval_service)],
) -> dict[str, object]:
    evidence = await service.retrieve(
        claims=claims,
        organization_id=organization_id,
        workspace_id=workspace_id,
        query=request.query,
        top_k=request.top_k,
    )
    return {
        "data": {
            "candidates": [candidate.as_dict() for candidate in evidence],
            "query": request.query,
        }
    }
