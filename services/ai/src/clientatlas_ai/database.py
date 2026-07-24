from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import TypeVar

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from clientatlas_ai.auth import VerifiedClaims
from clientatlas_ai.settings import get_settings

T = TypeVar("T")

_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_user_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is not None:
        return _session_factory

    settings = get_settings()
    engine = create_async_engine(
        str(settings.user_database_url),
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
    )
    _session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    return _session_factory


async def with_user_database(
    claims: VerifiedClaims,
    operation: Callable[[AsyncSession], Awaitable[T]],
) -> T:
    session_factory = get_user_session_factory()
    async with session_factory() as session:
        async with session.begin():
            await session.execute(
                text("select set_config('request.jwt.claims', :claims_json, true)"),
                {
                    "claims_json": json.dumps(
                        claims.database_payload(),
                        separators=(",", ":"),
                        sort_keys=True,
                    )
                },
            )

            # Fixed SQL identifier. Never derive this statement from request input.
            await session.execute(text("set local role authenticated"))
            return await operation(session)
