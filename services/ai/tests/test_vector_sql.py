from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from clientatlas_ai.chunking import DocumentChunk
from clientatlas_ai.ingestion_repository import activate_chunks
from clientatlas_ai.retrieval import hybrid_retrieve


@pytest.mark.asyncio
async def test_ingestion_qualifies_vector_type_schema() -> None:
    session = AsyncMock()

    await activate_chunks(
        session,
        source_id=uuid4(),
        version_id=uuid4(),
        organization_id=uuid4(),
        workspace_id=uuid4(),
        page_count=1,
        chunks=(
            DocumentChunk(
                content="Evidence",
                locator={"paragraph": 1},
                ordinal=0,
                token_count=2,
            ),
        ),
        embeddings=[[1.0, 0.0]],
    )

    statements = [str(call.args[0]) for call in session.execute.await_args_list]
    chunk_insert = next(
        statement
        for statement in statements
        if "insert into app.document_chunks" in statement
    )
    assert "cast(:embedding as extensions.vector)" in chunk_insert
    assert "cast(:embedding as vector)" not in chunk_insert


@pytest.mark.asyncio
async def test_retrieval_qualifies_vector_type_schema() -> None:
    session = AsyncMock()
    session.execute.return_value = []

    result = await hybrid_retrieve(
        session,
        organization_id=uuid4(),
        workspace_id=uuid4(),
        query="implementation owner",
        query_embedding=[1.0, 0.0],
        top_k=5,
    )

    assert result == ()
    statement = str(session.execute.await_args.args[0])
    assert statement.count("cast(:query_embedding as extensions.vector)") == 2
    assert "cast(:query_embedding as vector)" not in statement
