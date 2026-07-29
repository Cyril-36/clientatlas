from __future__ import annotations

import json
from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from clientatlas_ai.auth import VerifiedClaims, require_verified_claims
from clientatlas_ai.embeddings import (
    DeterministicEmbeddingProvider,
    EmbeddingProvider,
    HuggingFaceEmbeddingProvider,
)
from clientatlas_ai.generation import (
    AnswerService,
    DeterministicGenerationProvider,
    GeminiGenerationProvider,
    GenerationProvider,
    HuggingFaceGenerationProvider,
)
from clientatlas_ai.rate_limit import expensive_operation_limiter
from clientatlas_ai.retrieval import RetrievalService
from clientatlas_ai.settings import get_settings

router = APIRouter(
    prefix="/v1/organizations/{organization_id}/workspaces/{workspace_id}",
    tags=["chat"],
)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conversation_id: UUID | None = None
    question: str = Field(min_length=1, max_length=2_000)
    top_k: int = Field(default=8, ge=1, le=20)


def sse(event: str, data: dict[str, object]) -> bytes:
    encoded = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    return f"event: {event}\ndata: {encoded}\n\n".encode()


@lru_cache
def get_answer_service() -> AnswerService:
    settings = get_settings()
    embeddings: EmbeddingProvider
    local: GenerationProvider
    if settings.environment == "test":
        embeddings = DeterministicEmbeddingProvider(settings.embedding_dimensions)
        local = DeterministicGenerationProvider()
    else:
        embeddings = HuggingFaceEmbeddingProvider(
            model=settings.huggingface_embedding_model,
            device=settings.huggingface_embedding_device,
            dimensions=settings.embedding_dimensions,
            timeout_seconds=settings.llm_timeout_seconds,
        )
        local = HuggingFaceGenerationProvider(
            model=settings.huggingface_generation_model,
            device=settings.huggingface_generation_device,
            max_input_characters=settings.local_model_max_input_characters,
            max_new_tokens=settings.local_model_max_new_tokens,
            timeout_seconds=settings.llm_timeout_seconds,
        )
    synthetic = None
    if settings.gemini_api_key is not None:
        synthetic = GeminiGenerationProvider(
            api_key=settings.gemini_api_key.get_secret_value(),
            model=settings.gemini_model,
            timeout_seconds=settings.llm_timeout_seconds,
        )
    return AnswerService(
        retrieval=RetrievalService(embeddings),
        local_provider=local,
        synthetic_provider=synthetic,
    )


async def answer_events(
    service: AnswerService,
    *,
    claims: VerifiedClaims,
    organization_id: UUID,
    workspace_id: UUID,
    request: ChatRequest,
) -> AsyncIterator[bytes]:
    yield sse("progress", {"stage": "retrieving"})
    result = await service.answer(
        claims=claims,
        organization_id=organization_id,
        workspace_id=workspace_id,
        question=request.question,
        conversation_id=request.conversation_id,
        top_k=request.top_k,
    )
    yield sse(
        "answer",
        {
            "abstained": result.abstained,
            "content": result.answer,
            "contentFormat": "plain_text",
        },
    )
    for citation in result.citations:
        yield sse("citation", citation.as_dict())
    yield sse(
        "complete",
        {
            "conversationId": str(result.conversation_id),
            "messageId": str(result.message_id),
            "model": result.model,
            "provider": result.provider,
        },
    )


@router.post("/chat/stream")
async def stream_answer(
    organization_id: UUID,
    workspace_id: UUID,
    request: ChatRequest,
    claims: Annotated[VerifiedClaims, Depends(require_verified_claims)],
    service: Annotated[AnswerService, Depends(get_answer_service)],
) -> StreamingResponse:
    await expensive_operation_limiter.check(claims.subject, "chat")
    return StreamingResponse(
        answer_events(
            service,
            claims=claims,
            organization_id=organization_id,
            workspace_id=workspace_id,
            request=request,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store",
            "X-Accel-Buffering": "no",
            "X-Content-Type-Options": "nosniff",
        },
    )
