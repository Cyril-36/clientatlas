from __future__ import annotations

import hashlib
from dataclasses import dataclass
from uuid import UUID, uuid4

from clientatlas_ai.auth import VerifiedClaims
from clientatlas_ai.chunking import chunk_blocks
from clientatlas_ai.database import with_user_database
from clientatlas_ai.documents import parse_document, validate_document
from clientatlas_ai.embeddings import EmbeddingProvider
from clientatlas_ai.errors import SafeServiceError
from clientatlas_ai.ingestion_repository import (
    SourceVersion,
    activate_chunks,
    create_source_version,
    delete_source_records,
    get_source_version,
    mark_ingestion_failed,
    set_ingestion_state,
)
from clientatlas_ai.storage import LocalObjectStorage, generated_object_path
from clientatlas_ai.telemetry import INGESTION_FAILURES, tracer


@dataclass(frozen=True, slots=True)
class QueuedSource:
    checksum_sha256: str
    source_id: UUID
    version_id: UUID


class IngestionService:
    def __init__(
        self,
        *,
        storage: LocalObjectStorage,
        embeddings: EmbeddingProvider,
        max_upload_bytes: int,
    ) -> None:
        self._storage = storage
        self._embeddings = embeddings
        self._max_upload_bytes = max_upload_bytes

    async def queue_upload(
        self,
        *,
        claims: VerifiedClaims,
        organization_id: UUID,
        workspace_id: UUID,
        filename: str,
        declared_mime: str | None,
        content: bytes,
        kind: str = "upload",
        external_file_id: str | None = None,
    ) -> QueuedSource:
        mime_type = validate_document(
            filename,
            declared_mime,
            content,
            max_bytes=self._max_upload_bytes,
        )
        checksum = hashlib.sha256(content).hexdigest()
        source_id = uuid4()
        version_id = uuid4()
        object_path = generated_object_path(
            organization_id,
            workspace_id,
            source_id,
            version_id,
            filename,
        )
        await self._storage.put(object_path, content)

        async def create(session: object) -> SourceVersion:
            from sqlalchemy.ext.asyncio import AsyncSession

            assert isinstance(session, AsyncSession)
            return await create_source_version(
                session,
                organization_id=organization_id,
                workspace_id=workspace_id,
                source_id=source_id,
                version_id=version_id,
                actor_id=claims.subject,
                filename=filename,
                object_path=object_path,
                checksum=checksum,
                mime_type=mime_type,
                byte_size=len(content),
                embedding_provider=self._embeddings.name,
                embedding_model=self._embeddings.model,
                kind=kind,
                external_file_id=external_file_id,
            )

        try:
            await with_user_database(claims, create)
        except Exception:
            await self._storage.delete(object_path)
            raise
        return QueuedSource(
            checksum_sha256=checksum,
            source_id=source_id,
            version_id=version_id,
        )

    async def process(
        self,
        *,
        claims: VerifiedClaims,
        organization_id: UUID,
        workspace_id: UUID,
        source_id: UUID,
    ) -> None:
        async def lookup(session: object) -> SourceVersion | None:
            from sqlalchemy.ext.asyncio import AsyncSession

            assert isinstance(session, AsyncSession)
            return await get_source_version(
                session,
                organization_id=organization_id,
                workspace_id=workspace_id,
                source_id=source_id,
            )

        with tracer.start_as_current_span("ingestion.process") as span:
            source = await with_user_database(claims, lookup)
            if source is None:
                raise SafeServiceError("source_not_found", status_code=404)

            try:
                await self._state(claims, source, "parsing")
                content = await self._storage.get(source.object_path)
                suffix = source.object_path.rsplit(".", maxsplit=1)[-1]
                mime = (
                    "application/pdf"
                    if suffix == "pdf"
                    else "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                )
                parsed = parse_document(mime, content)
                await self._state(claims, source, "chunking")
                chunks = chunk_blocks(parsed.blocks)
                if not chunks:
                    raise SafeServiceError("no_extractable_text")
                await self._state(claims, source, "embedding")
                embeddings = await self._embeddings.embed(
                    [chunk.content for chunk in chunks]
                )

                async def activate(session: object) -> None:
                    from sqlalchemy.ext.asyncio import AsyncSession

                    assert isinstance(session, AsyncSession)
                    await activate_chunks(
                        session,
                        source_id=source.source_id,
                        version_id=source.version_id,
                        organization_id=organization_id,
                        workspace_id=workspace_id,
                        page_count=parsed.page_count,
                        chunks=chunks,
                        embeddings=embeddings,
                    )

                await with_user_database(claims, activate)
                span.set_attribute("ingestion.chunk_count", len(chunks))
                span.set_attribute("ingestion.provider", self._embeddings.name)
            except SafeServiceError as error:
                safe_error_code = error.code
                INGESTION_FAILURES.labels(code=safe_error_code).inc()

                async def fail(session: object) -> None:
                    from sqlalchemy.ext.asyncio import AsyncSession

                    assert isinstance(session, AsyncSession)
                    await mark_ingestion_failed(
                        session,
                        source_id=source.source_id,
                        version_id=source.version_id,
                        safe_error_code=safe_error_code,
                    )

                await with_user_database(claims, fail)
                raise

    async def _state(
        self,
        claims: VerifiedClaims,
        source: SourceVersion,
        state: str,
    ) -> None:
        async def update(session: object) -> None:
            from sqlalchemy.ext.asyncio import AsyncSession

            assert isinstance(session, AsyncSession)
            await set_ingestion_state(
                session,
                source_id=source.source_id,
                version_id=source.version_id,
                state=state,
            )

        await with_user_database(claims, update)

    async def delete(
        self,
        *,
        claims: VerifiedClaims,
        organization_id: UUID,
        workspace_id: UUID,
        source_id: UUID,
    ) -> bool:
        async def remove(session: object) -> str | None:
            from sqlalchemy.ext.asyncio import AsyncSession

            assert isinstance(session, AsyncSession)
            return await delete_source_records(
                session,
                organization_id=organization_id,
                workspace_id=workspace_id,
                source_id=source_id,
            )

        object_path = await with_user_database(claims, remove)
        if object_path is None:
            return False
        await self._storage.delete(object_path)
        return True
