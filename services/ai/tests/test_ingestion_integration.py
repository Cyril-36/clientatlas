from __future__ import annotations

import io
import os
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TypeVar
from uuid import UUID, uuid4

import pytest
from anyio import to_thread
from docx import Document
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from clientatlas_ai import database
from clientatlas_ai.auth import VerifiedClaims
from clientatlas_ai.documents import DOCX_MIME
from clientatlas_ai.embeddings import DeterministicEmbeddingProvider
from clientatlas_ai.ingestion import IngestionService
from clientatlas_ai.storage import LocalObjectStorage

T = TypeVar("T")
MIGRATION_URL = os.getenv("CLIENTATLAS_TEST_MIGRATION_DATABASE_URL")
USER_URL = os.getenv("CLIENTATLAS_TEST_USER_DATABASE_URL")

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.integration,
    pytest.mark.skipif(
        not MIGRATION_URL or not USER_URL,
        reason="PostgreSQL integration URLs are not configured",
    ),
]


def docx_bytes(text_value: str) -> bytes:
    document = Document()
    document.add_paragraph(text_value)
    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


def claims_for(user_id: UUID) -> VerifiedClaims:
    return VerifiedClaims(
        audience="authenticated",
        expires_at=4_102_444_800,
        issuer="https://test.supabase.co/auth/v1",
        role="authenticated",
        subject=user_id,
    )


async def test_docx_ingestion_retrieval_visibility_and_deletion(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    assert MIGRATION_URL is not None
    assert USER_URL is not None
    migration_engine = create_async_engine(MIGRATION_URL)
    user_engine = create_async_engine(USER_URL, pool_size=1, max_overflow=0)
    user_factory = async_sessionmaker(user_engine, expire_on_commit=False)
    monkeypatch.setattr(database, "_session_factory", user_factory)

    user_a, user_b = uuid4(), uuid4()
    organization_id: UUID | None = None
    workspace_id: UUID | None = None
    service = IngestionService(
        storage=LocalObjectStorage(tmp_path),
        embeddings=DeterministicEmbeddingProvider(),
        max_upload_bytes=1_000_000,
    )

    async def as_user(
        claims: VerifiedClaims,
        operation: Callable[[AsyncSession], Awaitable[T]],
    ) -> T:
        return await database.with_user_database(claims, operation)

    try:
        async with migration_engine.begin() as connection:
            await connection.execute(
                text(
                    "insert into auth.users (id, email) values "
                    "(:user_a, :email_a), (:user_b, :email_b)"
                ),
                {
                    "email_a": f"ingest-a-{user_a}@example.test",
                    "email_b": f"ingest-b-{user_b}@example.test",
                    "user_a": user_a,
                    "user_b": user_b,
                },
            )

        async def create_workspace(session: AsyncSession) -> tuple[UUID, UUID]:
            org_result = await session.execute(
                text("select app.create_organization(:name, :slug)"),
                {
                    "name": "Ingestion tenant",
                    "slug": f"ingestion-{user_a}",
                },
            )
            org_id = UUID(str(org_result.scalar_one()))
            workspace_result = await session.execute(
                text(
                    """
                    insert into app.workspaces (
                      organization_id, name, privacy_mode, created_by
                    )
                    values (:org_id, 'Client', 'local_confidential', :user_id)
                    returning id
                    """
                ),
                {"org_id": org_id, "user_id": user_a},
            )
            return org_id, UUID(str(workspace_result.scalar_one()))

        organization_id, workspace_id = await as_user(
            claims_for(user_a),
            create_workspace,
        )
        queued = await service.queue_upload(
            claims=claims_for(user_a),
            organization_id=organization_id,
            workspace_id=workspace_id,
            filename="brief.docx",
            declared_mime=DOCX_MIME,
            content=docx_bytes("The implementation owner is Avery."),
        )
        await service.process(
            claims=claims_for(user_a),
            organization_id=organization_id,
            workspace_id=workspace_id,
            source_id=queued.source_id,
        )

        async def source_state(session: AsyncSession) -> tuple[str, int]:
            result = await session.execute(
                text(
                    """
                    select source.state::text, count(chunk.id)
                    from app.sources source
                    left join app.document_chunks chunk
                      on chunk.source_id = source.id
                    where source.id = :source_id
                    group by source.state
                    """
                ),
                {"source_id": queued.source_id},
            )
            row = result.one()
            return str(row[0]), int(row[1])

        state, count = await as_user(claims_for(user_a), source_state)
        assert state == "ready"
        assert count == 1

        async def visible_to_other(session: AsyncSession) -> int:
            result = await session.execute(
                text("select count(*) from app.sources where id = :source_id"),
                {"source_id": queued.source_id},
            )
            return int(result.scalar_one())

        assert await as_user(claims_for(user_b), visible_to_other) == 0
        assert await service.delete(
            claims=claims_for(user_a),
            organization_id=organization_id,
            workspace_id=workspace_id,
            source_id=queued.source_id,
        )
        remaining = await to_thread.run_sync(lambda: list(tmp_path.rglob("*.docx")))
        assert not remaining
    finally:
        async with migration_engine.begin() as connection:
            if organization_id is not None:
                await connection.execute(
                    text("delete from app.organizations where id = :id"),
                    {"id": organization_id},
                )
            await connection.execute(
                text("delete from auth.users where id in (:user_a, :user_b)"),
                {"user_a": user_a, "user_b": user_b},
            )
        await user_engine.dispose()
        await migration_engine.dispose()
