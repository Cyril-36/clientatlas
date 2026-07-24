from __future__ import annotations

from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from clientatlas_ai.artifacts import (
    ArtifactProvider,
    ArtifactResult,
    ArtifactService,
    ArtifactStatus,
    ArtifactType,
    DeterministicArtifactProvider,
    OllamaArtifactProvider,
    list_artifact_versions,
    list_artifacts,
)
from clientatlas_ai.auth import VerifiedClaims, require_verified_claims
from clientatlas_ai.database import with_user_database
from clientatlas_ai.embeddings import (
    DeterministicEmbeddingProvider,
    EmbeddingProvider,
    OllamaEmbeddingProvider,
)
from clientatlas_ai.retrieval import RetrievalService
from clientatlas_ai.settings import get_settings

router = APIRouter(
    prefix="/v1/organizations/{organization_id}/workspaces/{workspace_id}/artifacts",
    tags=["artifacts"],
)


class GenerateArtifactRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_type: ArtifactType
    title: str = Field(min_length=1, max_length=200)


class SaveArtifactVersionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_type: ArtifactType
    content: dict[str, object]
    status: ArtifactStatus = "draft"


def result_payload(result: ArtifactResult) -> dict[str, object]:
    return {
        "artifactId": str(result.artifact_id),
        "content": result.content,
        "status": result.status,
        "versionId": str(result.version_id),
        "versionNumber": result.version_number,
    }


@lru_cache
def get_artifact_service() -> ArtifactService:
    settings = get_settings()
    embeddings: EmbeddingProvider
    provider: ArtifactProvider
    if settings.environment == "test":
        embeddings = DeterministicEmbeddingProvider(settings.embedding_dimensions)
        provider = DeterministicArtifactProvider()
    else:
        embeddings = OllamaEmbeddingProvider(
            base_url=str(settings.ollama_base_url),
            model=settings.ollama_embedding_model,
            dimensions=settings.embedding_dimensions,
            timeout_seconds=settings.llm_timeout_seconds,
        )
        provider = OllamaArtifactProvider(
            base_url=str(settings.ollama_base_url),
            model=settings.ollama_generation_model,
            timeout_seconds=settings.llm_timeout_seconds,
        )
    return ArtifactService(
        retrieval=RetrievalService(embeddings),
        provider=provider,
    )


@router.post("/generate", status_code=201)
async def generate_artifact(
    organization_id: UUID,
    workspace_id: UUID,
    request: GenerateArtifactRequest,
    claims: Annotated[VerifiedClaims, Depends(require_verified_claims)],
    service: Annotated[ArtifactService, Depends(get_artifact_service)],
) -> dict[str, object]:
    result = await service.generate(
        claims=claims,
        organization_id=organization_id,
        workspace_id=workspace_id,
        artifact_type=request.artifact_type,
        title=request.title,
    )
    return {"data": result_payload(result)}


@router.get("")
async def get_artifacts(
    organization_id: UUID,
    workspace_id: UUID,
    claims: Annotated[VerifiedClaims, Depends(require_verified_claims)],
) -> dict[str, object]:
    async def query(session: AsyncSession) -> list[dict[str, object]]:
        return await list_artifacts(
            session,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )

    return {"data": await with_user_database(claims, query)}


@router.get("/{artifact_id}/versions")
async def get_artifact_versions(
    organization_id: UUID,
    workspace_id: UUID,
    artifact_id: UUID,
    claims: Annotated[VerifiedClaims, Depends(require_verified_claims)],
) -> dict[str, object]:
    async def query(session: AsyncSession) -> list[dict[str, object]]:
        return await list_artifact_versions(
            session,
            organization_id=organization_id,
            workspace_id=workspace_id,
            artifact_id=artifact_id,
        )

    return {"data": await with_user_database(claims, query)}


@router.post("/{artifact_id}/versions", status_code=201)
async def save_artifact_version(
    organization_id: UUID,
    workspace_id: UUID,
    artifact_id: UUID,
    request: SaveArtifactVersionRequest,
    claims: Annotated[VerifiedClaims, Depends(require_verified_claims)],
    service: Annotated[ArtifactService, Depends(get_artifact_service)],
) -> dict[str, object]:
    result = await service.save_edited_version(
        claims=claims,
        organization_id=organization_id,
        workspace_id=workspace_id,
        artifact_id=artifact_id,
        artifact_type=request.artifact_type,
        content_payload=request.content,
        status=request.status,
    )
    return {"data": result_payload(result)}
