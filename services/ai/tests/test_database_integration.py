from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from clientatlas_ai import database
from clientatlas_ai.auth import VerifiedClaims

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


async def scalar(
    session: AsyncSession,
    statement: str,
    parameters: dict[str, Any] | None = None,
) -> Any:
    result = await session.execute(text(statement), parameters or {})
    return result.scalar_one()


async def run_as_user(
    claims: VerifiedClaims,
    operation: Callable[[AsyncSession], Awaitable[T]],
) -> T:
    return await database.with_user_database(claims, operation)


async def test_python_transaction_contract_and_tenant_isolation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert MIGRATION_URL is not None
    assert USER_URL is not None

    migration_engine = create_async_engine(MIGRATION_URL)
    user_engine = create_async_engine(USER_URL, pool_size=1, max_overflow=0)
    user_factory = async_sessionmaker(
        user_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    monkeypatch.setattr(database, "_session_factory", user_factory)

    user_a = uuid4()
    user_b = uuid4()
    organization_id: str | None = None

    try:
        async with migration_engine.begin() as connection:
            await connection.execute(
                text(
                    "insert into auth.users (id, email) values "
                    "(:user_a, :email_a), (:user_b, :email_b)"
                ),
                {
                    "email_a": f"python-a-{user_a}@example.test",
                    "email_b": f"python-b-{user_b}@example.test",
                    "user_a": user_a,
                    "user_b": user_b,
                },
            )

        claims_a = VerifiedClaims(
            audience="authenticated",
            expires_at=4_102_444_800,
            issuer="https://test.supabase.co/auth/v1",
            role="authenticated",
            subject=user_a,
        )
        claims_b = VerifiedClaims(
            audience="authenticated",
            expires_at=4_102_444_800,
            issuer="https://test.supabase.co/auth/v1",
            role="authenticated",
            subject=user_b,
        )

        async def create_tenant(session: AsyncSession) -> str:
            return str(
                await scalar(
                    session,
                    "select app.create_organization(:name, :slug)",
                    {
                        "name": f"Python tenant {user_a}",
                        "slug": f"python-tenant-{user_a}",
                    },
                )
            )

        organization_id = await run_as_user(claims_a, create_tenant)

        async def inspect_context(session: AsyncSession) -> tuple[str, str]:
            result = await session.execute(
                text("select current_role, auth.uid()::text as user_id")
            )
            row = result.one()
            return str(row.current_role), str(row.user_id)

        assert await run_as_user(claims_a, inspect_context) == (
            "authenticated",
            str(user_a),
        )

        async def visible_organizations(session: AsyncSession) -> int:
            result = await session.execute(
                text("select count(*) from app.organizations where id = :id"),
                {"id": organization_id},
            )
            return int(result.scalar_one())

        assert await run_as_user(claims_a, visible_organizations) == 1
        assert await run_as_user(claims_b, visible_organizations) == 0

        async with user_factory() as session:
            result = await session.execute(
                text(
                    "select current_role, "
                    "nullif(current_setting("
                    "'request.jwt.claims', true), '') as claims"
                )
            )
            row = result.one()
            assert row.current_role == "clientatlas_runtime"
            assert row.claims is None
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
