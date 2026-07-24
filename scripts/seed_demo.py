from __future__ import annotations

import asyncio
import io
import os
from pathlib import Path
from uuid import UUID

from clientatlas_ai.auth import VerifiedClaims
from clientatlas_ai.database import with_user_database
from clientatlas_ai.embeddings import DeterministicEmbeddingProvider
from clientatlas_ai.ingestion import IngestionService
from clientatlas_ai.storage import LocalObjectStorage
from docx import Document
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

DEMO_USER_ID = UUID("00000000-0000-4000-8000-000000000001")
CORPUS = Path("packages/evaluation/corpus")


def to_docx(source: Path) -> bytes:
    document = Document()
    for block in source.read_text(encoding="utf-8").split("\n\n"):
        value = block.strip().lstrip("#").strip()
        if value:
            document.add_paragraph(value)
    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


async def main() -> None:
    migration_url = os.environ["CLIENTATLAS_TEST_MIGRATION_DATABASE_URL"]
    migration_engine = create_async_engine(migration_url)
    async with migration_engine.begin() as connection:
        await connection.execute(
            text(
                """
                insert into auth.users (id, email)
                values (:id, 'demo@clientatlas.invalid')
                on conflict (id) do nothing
                """
            ),
            {"id": DEMO_USER_ID},
        )
    await migration_engine.dispose()

    claims = VerifiedClaims(
        audience="authenticated",
        expires_at=4_102_444_800,
        issuer="https://local.clientatlas.invalid/auth/v1",
        role="authenticated",
        subject=DEMO_USER_ID,
    )

    async def ensure_workspace(session: AsyncSession) -> tuple[UUID, UUID]:
        existing = await session.execute(
            text("select id from app.organizations where slug = 'northstar-demo'")
        )
        organization_id = existing.scalar_one_or_none()
        if organization_id is None:
            created = await session.execute(
                text(
                    "select app.create_organization("
                    "'Northstar Labs Demo', 'northstar-demo')"
                )
            )
            organization_id = created.scalar_one()
        workspace = await session.execute(
            text(
                """
                select id from app.workspaces
                where organization_id = :organization_id
                  and name = 'Synthetic Onboarding'
                """
            ),
            {"organization_id": organization_id},
        )
        workspace_id = workspace.scalar_one_or_none()
        if workspace_id is None:
            created_workspace = await session.execute(
                text(
                    """
                    insert into app.workspaces (
                      organization_id, name, privacy_mode, created_by
                    )
                    values (
                      :organization_id, 'Synthetic Onboarding',
                      'synthetic_demo', :user_id
                    )
                    returning id
                    """
                ),
                {"organization_id": organization_id, "user_id": DEMO_USER_ID},
            )
            workspace_id = created_workspace.scalar_one()
        return UUID(str(organization_id)), UUID(str(workspace_id))

    organization_id, workspace_id = await with_user_database(
        claims,
        ensure_workspace,
    )
    service = IngestionService(
        storage=LocalObjectStorage(Path(".clientatlas/storage")),
        embeddings=DeterministicEmbeddingProvider(),
        max_upload_bytes=25 * 1024 * 1024,
    )
    for source in sorted(CORPUS.glob("*.md")):
        filename = f"{source.stem}.docx"

        async def exists(
            session: AsyncSession,
            target_filename: str = filename,
        ) -> bool:
            result = await session.execute(
                text(
                    """
                    select exists (
                      select 1 from app.sources
                      where organization_id = :organization_id
                        and workspace_id = :workspace_id
                        and display_name = :filename
                        and deleted_at is null
                    )
                    """
                ),
                {
                    "filename": target_filename,
                    "organization_id": organization_id,
                    "workspace_id": workspace_id,
                },
            )
            return bool(result.scalar_one())

        if await with_user_database(claims, exists):
            continue
        queued = await service.queue_upload(
            claims=claims,
            organization_id=organization_id,
            workspace_id=workspace_id,
            filename=filename,
            declared_mime=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            content=to_docx(source),
        )
        await service.process(
            claims=claims,
            organization_id=organization_id,
            workspace_id=workspace_id,
            source_id=queued.source_id,
        )
    print(
        f"organization={organization_id} workspace={workspace_id} user={DEMO_USER_ID}"
    )


if __name__ == "__main__":
    asyncio.run(main())
