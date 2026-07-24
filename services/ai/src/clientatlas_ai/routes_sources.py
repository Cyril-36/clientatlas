from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from clientatlas_ai.auth import VerifiedClaims, require_verified_claims
from clientatlas_ai.database import with_user_database
from clientatlas_ai.dependencies import get_ingestion_service
from clientatlas_ai.errors import SafeServiceError
from clientatlas_ai.ingestion import IngestionService
from clientatlas_ai.ingestion_repository import list_sources
from clientatlas_ai.settings import get_settings

router = APIRouter(
    prefix="/v1/organizations/{organization_id}/workspaces/{workspace_id}/sources",
    tags=["sources"],
)


async def _process_safely(
    service: IngestionService,
    claims: VerifiedClaims,
    organization_id: UUID,
    workspace_id: UUID,
    source_id: UUID,
) -> None:
    try:
        await service.process(
            claims=claims,
            organization_id=organization_id,
            workspace_id=workspace_id,
            source_id=source_id,
        )
    except SafeServiceError:
        # The service persists a stable failure code before returning.
        return


@router.get("")
async def get_sources(
    organization_id: UUID,
    workspace_id: UUID,
    claims: Annotated[VerifiedClaims, Depends(require_verified_claims)],
) -> dict[str, object]:
    async def query(session: AsyncSession) -> list[dict[str, object]]:
        return await list_sources(
            session,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )

    sources = await with_user_database(claims, query)
    return {"data": sources}


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def upload_source(
    organization_id: UUID,
    workspace_id: UUID,
    background_tasks: BackgroundTasks,
    claims: Annotated[VerifiedClaims, Depends(require_verified_claims)],
    service: Annotated[IngestionService, Depends(get_ingestion_service)],
    file: Annotated[UploadFile, File()],
) -> dict[str, object]:
    settings = get_settings()
    content = await file.read(settings.max_upload_bytes + 1)
    queued = await service.queue_upload(
        claims=claims,
        organization_id=organization_id,
        workspace_id=workspace_id,
        filename=file.filename or "unnamed",
        declared_mime=file.content_type,
        content=content,
    )
    background_tasks.add_task(
        _process_safely,
        service,
        claims,
        organization_id,
        workspace_id,
        queued.source_id,
    )
    return {
        "data": {
            "checksumSha256": queued.checksum_sha256,
            "sourceId": str(queued.source_id),
            "state": "queued",
            "versionId": str(queued.version_id),
        }
    }


@router.post("/{source_id}/reindex", status_code=status.HTTP_202_ACCEPTED)
async def reindex_source(
    organization_id: UUID,
    workspace_id: UUID,
    source_id: UUID,
    background_tasks: BackgroundTasks,
    claims: Annotated[VerifiedClaims, Depends(require_verified_claims)],
    service: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> dict[str, object]:
    background_tasks.add_task(
        _process_safely,
        service,
        claims,
        organization_id,
        workspace_id,
        source_id,
    )
    return {"data": {"sourceId": str(source_id), "state": "queued"}}


@router.delete("/{source_id}")
async def delete_source(
    organization_id: UUID,
    workspace_id: UUID,
    source_id: UUID,
    claims: Annotated[VerifiedClaims, Depends(require_verified_claims)],
    service: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> dict[str, object]:
    deleted = await service.delete(
        claims=claims,
        organization_id=organization_id,
        workspace_id=workspace_id,
        source_id=source_id,
    )
    return {"data": {"deleted": deleted, "sourceId": str(source_id)}}
