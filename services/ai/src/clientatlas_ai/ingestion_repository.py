from __future__ import annotations

import json
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from clientatlas_ai.chunking import DocumentChunk


@dataclass(frozen=True, slots=True)
class SourceVersion:
    object_path: str
    source_id: UUID
    version_id: UUID


async def create_source_version(
    session: AsyncSession,
    *,
    organization_id: UUID,
    workspace_id: UUID,
    source_id: UUID,
    version_id: UUID,
    actor_id: UUID,
    filename: str,
    object_path: str,
    checksum: str,
    mime_type: str,
    byte_size: int,
    embedding_provider: str,
    embedding_model: str,
    kind: str = "upload",
    external_file_id: str | None = None,
) -> SourceVersion:
    await session.execute(
        text(
            """
            insert into app.sources (
              id, organization_id, workspace_id, kind, display_name,
              external_file_id, object_path, state, created_by
            )
            values (
              :source_id, :organization_id, :workspace_id,
              cast(:kind as app.source_kind), :filename,
              :external_file_id, :object_path, 'queued', :actor_id
            )
            """
        ),
        {
            "actor_id": actor_id,
            "external_file_id": external_file_id,
            "filename": filename,
            "kind": kind,
            "object_path": object_path,
            "organization_id": organization_id,
            "source_id": source_id,
            "workspace_id": workspace_id,
        },
    )
    await session.execute(
        text(
            """
            insert into app.document_versions (
              id, organization_id, workspace_id, source_id, checksum_sha256,
              mime_type, byte_size, parser_version, embedding_provider,
              embedding_model, state, created_by
            )
            values (
              :version_id, :organization_id, :workspace_id, :source_id,
              :checksum, :mime_type, :byte_size, 'clientatlas-parser-1',
              :embedding_provider, :embedding_model, 'queued', :actor_id
            )
            """
        ),
        {
            "actor_id": actor_id,
            "byte_size": byte_size,
            "checksum": checksum,
            "embedding_model": embedding_model,
            "embedding_provider": embedding_provider,
            "mime_type": mime_type,
            "organization_id": organization_id,
            "source_id": source_id,
            "version_id": version_id,
            "workspace_id": workspace_id,
        },
    )
    await session.execute(
        text(
            """
            insert into app.ingestion_jobs (
              organization_id, workspace_id, source_id, document_version_id
            )
            values (
              :organization_id, :workspace_id, :source_id, :version_id
            )
            """
        ),
        {
            "organization_id": organization_id,
            "source_id": source_id,
            "version_id": version_id,
            "workspace_id": workspace_id,
        },
    )
    return SourceVersion(
        object_path=object_path,
        source_id=source_id,
        version_id=version_id,
    )


async def list_sources(
    session: AsyncSession,
    *,
    organization_id: UUID,
    workspace_id: UUID,
) -> list[dict[str, object]]:
    result = await session.execute(
        text(
            """
            select
              id, display_name, kind::text as kind, state::text as state,
              active_version_id, safe_error_code, created_at, updated_at
            from app.sources
            where organization_id = :organization_id
              and workspace_id = :workspace_id
              and deleted_at is null
            order by created_at desc
            """
        ),
        {
            "organization_id": organization_id,
            "workspace_id": workspace_id,
        },
    )
    return [dict(row._mapping) for row in result]


async def get_source_version(
    session: AsyncSession,
    *,
    organization_id: UUID,
    workspace_id: UUID,
    source_id: UUID,
) -> SourceVersion | None:
    result = await session.execute(
        text(
            """
            select
              source.object_path,
              source.id as source_id,
              version.id as version_id
            from app.sources source
            join app.document_versions version
              on version.source_id = source.id
            where source.organization_id = :organization_id
              and source.workspace_id = :workspace_id
              and source.id = :source_id
              and source.deleted_at is null
            order by version.created_at desc
            limit 1
            """
        ),
        {
            "organization_id": organization_id,
            "source_id": source_id,
            "workspace_id": workspace_id,
        },
    )
    row = result.first()
    if row is None:
        return None
    return SourceVersion(
        object_path=str(row.object_path),
        source_id=UUID(str(row.source_id)),
        version_id=UUID(str(row.version_id)),
    )


async def set_ingestion_state(
    session: AsyncSession,
    *,
    source_id: UUID,
    version_id: UUID,
    state: str,
    safe_error_code: str | None = None,
) -> None:
    await session.execute(
        text(
            """
            update app.sources
            set state = cast(:state as app.ingestion_state),
                safe_error_code = :safe_error_code,
                updated_at = now()
            where id = :source_id
            """
        ),
        {
            "safe_error_code": safe_error_code,
            "source_id": source_id,
            "state": state,
        },
    )
    await session.execute(
        text(
            """
            update app.document_versions
            set state = cast(:state as app.ingestion_state),
                safe_error_code = :safe_error_code
            where id = :version_id
            """
        ),
        {
            "safe_error_code": safe_error_code,
            "state": state,
            "version_id": version_id,
        },
    )


async def activate_chunks(
    session: AsyncSession,
    *,
    source_id: UUID,
    version_id: UUID,
    organization_id: UUID,
    workspace_id: UUID,
    page_count: int | None,
    chunks: tuple[DocumentChunk, ...],
    embeddings: list[list[float]],
) -> None:
    await session.execute(
        text("delete from app.document_chunks where document_version_id = :version_id"),
        {"version_id": version_id},
    )
    statement = text(
        """
        insert into app.document_chunks (
          organization_id, workspace_id, source_id, document_version_id,
          ordinal, content, token_count, locator, embedding
        )
        values (
          :organization_id, :workspace_id, :source_id, :version_id,
          :ordinal, :content, :token_count, cast(:locator as jsonb),
          cast(:embedding as vector)
        )
        """
    )
    for chunk, embedding in zip(chunks, embeddings, strict=True):
        vector = "[" + ",".join(f"{value:.9g}" for value in embedding) + "]"
        await session.execute(
            statement,
            {
                "content": chunk.content,
                "embedding": vector,
                "locator": json.dumps(chunk.locator, separators=(",", ":")),
                "ordinal": chunk.ordinal,
                "organization_id": organization_id,
                "source_id": source_id,
                "token_count": chunk.token_count,
                "version_id": version_id,
                "workspace_id": workspace_id,
            },
        )
    await session.execute(
        text(
            """
            update app.document_versions
            set state = 'ready',
                chunk_count = :chunk_count,
                page_count = :page_count,
                safe_error_code = null,
                ready_at = now()
            where id = :version_id
            """
        ),
        {
            "chunk_count": len(chunks),
            "page_count": page_count,
            "version_id": version_id,
        },
    )
    await session.execute(
        text(
            """
            update app.sources
            set state = 'ready',
                active_version_id = :version_id,
                safe_error_code = null,
                updated_at = now()
            where id = :source_id
            """
        ),
        {"source_id": source_id, "version_id": version_id},
    )
    await session.execute(
        text(
            """
            update app.ingestion_jobs
            set state = 'complete', updated_at = now(), safe_error_code = null
            where document_version_id = :version_id
            """
        ),
        {"version_id": version_id},
    )


async def mark_ingestion_failed(
    session: AsyncSession,
    *,
    source_id: UUID,
    version_id: UUID,
    safe_error_code: str,
) -> None:
    await set_ingestion_state(
        session,
        source_id=source_id,
        version_id=version_id,
        state="failed",
        safe_error_code=safe_error_code,
    )
    await session.execute(
        text(
            """
            update app.ingestion_jobs
            set
              attempt_count = attempt_count + 1,
              state = case when attempt_count + 1 >= 3 then 'failed'
                           else 'retry' end,
              run_after = now() + make_interval(
                secs => least(300, power(2, attempt_count + 1)::integer * 5)
              ),
              safe_error_code = :safe_error_code,
              updated_at = now()
            where document_version_id = :version_id
            """
        ),
        {"safe_error_code": safe_error_code, "version_id": version_id},
    )


async def delete_source_records(
    session: AsyncSession,
    *,
    organization_id: UUID,
    workspace_id: UUID,
    source_id: UUID,
) -> str | None:
    result = await session.execute(
        text(
            """
            select object_path
            from app.sources
            where organization_id = :organization_id
              and workspace_id = :workspace_id
              and id = :source_id
            for update
            """
        ),
        {
            "organization_id": organization_id,
            "source_id": source_id,
            "workspace_id": workspace_id,
        },
    )
    row = result.first()
    if row is None:
        return None
    await session.execute(
        text(
            """
            update app.sources
            set state = 'deleting', active_version_id = null, updated_at = now()
            where id = :source_id
            """
        ),
        {"source_id": source_id},
    )
    await session.execute(
        text("delete from app.document_versions where source_id = :source_id"),
        {"source_id": source_id},
    )
    await session.execute(
        text(
            """
            update app.sources
            set state = 'deleted', deleted_at = now(), updated_at = now()
            where id = :source_id
            """
        ),
        {"source_id": source_id},
    )
    return str(row.object_path)
