from __future__ import annotations

from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, ConfigDict, Field

from clientatlas_ai.auth import VerifiedClaims, require_verified_claims
from clientatlas_ai.dependencies import get_ingestion_service
from clientatlas_ai.errors import SafeServiceError
from clientatlas_ai.google_drive import (
    GoogleDriveConnector,
    GoogleOAuthClient,
    TokenCipher,
)
from clientatlas_ai.ingestion import IngestionService
from clientatlas_ai.rate_limit import expensive_operation_limiter
from clientatlas_ai.routes_sources import _process_safely
from clientatlas_ai.settings import get_settings

router = APIRouter(
    prefix="/v1/organizations/{organization_id}/workspaces/{workspace_id}"
    "/connectors/google-drive",
    tags=["google-drive"],
)


class OAuthCallbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=4_096)
    state: str = Field(min_length=32, max_length=512)


class ImportDriveFileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_id: str = Field(min_length=1, max_length=512, pattern=r"^[A-Za-z0-9_-]+$")


@lru_cache
def get_google_drive_connector() -> GoogleDriveConnector:
    settings = get_settings()
    if (
        settings.google_oauth_client_id is None
        or settings.google_oauth_client_secret is None
        or settings.google_oauth_redirect_uri is None
        or settings.token_encryption_key is None
    ):
        raise SafeServiceError("google_drive_not_configured", status_code=503)
    redirect_uri = str(settings.google_oauth_redirect_uri)
    oauth = GoogleOAuthClient(
        client_id=settings.google_oauth_client_id,
        client_secret=settings.google_oauth_client_secret.get_secret_value(),
        redirect_uri=redirect_uri,
        timeout_seconds=settings.llm_timeout_seconds,
    )
    return GoogleDriveConnector(
        oauth=oauth,
        cipher=TokenCipher(settings.token_encryption_key.get_secret_value()),
        redirect_uri=redirect_uri,
    )


@router.post("/authorize")
async def authorize_google_drive(
    organization_id: UUID,
    workspace_id: UUID,
    claims: Annotated[VerifiedClaims, Depends(require_verified_claims)],
    connector: Annotated[GoogleDriveConnector, Depends(get_google_drive_connector)],
) -> dict[str, object]:
    result = await connector.begin(
        claims=claims,
        organization_id=organization_id,
        workspace_id=workspace_id,
    )
    return {
        "data": {
            "authorizationUrl": result.authorization_url,
            "expiresAt": result.expires_at.isoformat(),
        }
    }


@router.post("/callback")
async def complete_google_drive(
    organization_id: UUID,
    workspace_id: UUID,
    request: OAuthCallbackRequest,
    claims: Annotated[VerifiedClaims, Depends(require_verified_claims)],
    connector: Annotated[GoogleDriveConnector, Depends(get_google_drive_connector)],
) -> dict[str, object]:
    connection_id = await connector.complete(
        claims=claims,
        expected_organization_id=organization_id,
        expected_workspace_id=workspace_id,
        state=request.state,
        code=request.code,
    )
    # The state record, not request path input, binds the resulting workspace.
    return {
        "data": {
            "connectionId": str(connection_id),
            "requestedOrganizationId": str(organization_id),
            "requestedWorkspaceId": str(workspace_id),
            "status": "active",
        }
    }


@router.post("/import", status_code=202)
async def import_google_drive_file(
    organization_id: UUID,
    workspace_id: UUID,
    request: ImportDriveFileRequest,
    background_tasks: BackgroundTasks,
    claims: Annotated[VerifiedClaims, Depends(require_verified_claims)],
    connector: Annotated[GoogleDriveConnector, Depends(get_google_drive_connector)],
    ingestion: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> dict[str, object]:
    await expensive_operation_limiter.check(claims.subject, "drive_import")
    settings = get_settings()
    drive_file = await connector.download_selected_file(
        claims=claims,
        organization_id=organization_id,
        workspace_id=workspace_id,
        file_id=request.file_id,
        max_bytes=settings.max_upload_bytes,
    )
    queued = await ingestion.queue_upload(
        claims=claims,
        organization_id=organization_id,
        workspace_id=workspace_id,
        filename=drive_file.filename,
        declared_mime=drive_file.mime_type,
        content=drive_file.content,
        kind="google_drive",
        external_file_id=drive_file.file_id,
    )
    background_tasks.add_task(
        _process_safely,
        ingestion,
        claims,
        organization_id,
        workspace_id,
        queued.source_id,
    )
    return {
        "data": {
            "sourceId": str(queued.source_id),
            "state": "queued",
            "versionId": str(queued.version_id),
        }
    }


@router.delete("")
async def revoke_google_drive(
    organization_id: UUID,
    workspace_id: UUID,
    claims: Annotated[VerifiedClaims, Depends(require_verified_claims)],
    connector: Annotated[GoogleDriveConnector, Depends(get_google_drive_connector)],
) -> dict[str, object]:
    revoked = await connector.revoke(
        claims=claims,
        organization_id=organization_id,
        workspace_id=workspace_id,
    )
    return {"data": {"revoked": revoked}}
