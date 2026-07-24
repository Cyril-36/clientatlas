from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from clientatlas_ai.auth import VerifiedClaims
from clientatlas_ai.database import with_user_database
from clientatlas_ai.embeddings import EmbeddingProvider
from clientatlas_ai.telemetry import RETRIEVAL_CANDIDATES, tracer

RRF_K = 60
MAX_CANDIDATES_PER_PATH = 40


@dataclass(frozen=True, slots=True)
class EvidenceChunk:
    chunk_id: UUID
    content: str
    fused_score: float
    lexical_rank: int | None
    locator: dict[str, object]
    semantic_rank: int | None
    source_id: UUID
    source_name: str
    version_id: UUID

    def as_dict(self) -> dict[str, object]:
        return {
            "chunkId": str(self.chunk_id),
            "content": self.content,
            "fusedScore": self.fused_score,
            "lexicalRank": self.lexical_rank,
            "locator": self.locator,
            "semanticRank": self.semantic_rank,
            "sourceId": str(self.source_id),
            "sourceName": self.source_name,
            "versionId": str(self.version_id),
        }


def vector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(f"{value:.9g}" for value in embedding) + "]"


async def hybrid_retrieve(
    session: AsyncSession,
    *,
    organization_id: UUID,
    workspace_id: UUID,
    query: str,
    query_embedding: list[float],
    top_k: int,
) -> tuple[EvidenceChunk, ...]:
    result = await session.execute(
        text(
            """
            with eligible as (
              select
                chunk.id,
                chunk.source_id,
                chunk.document_version_id,
                chunk.content,
                chunk.locator,
                chunk.content_tsv,
                chunk.embedding,
                source.display_name
              from app.document_chunks chunk
              join app.sources source
                on source.id = chunk.source_id
               and source.organization_id = chunk.organization_id
               and source.workspace_id = chunk.workspace_id
               and source.active_version_id = chunk.document_version_id
              where chunk.organization_id = :organization_id
                and chunk.workspace_id = :workspace_id
                and source.state = 'ready'
                and source.deleted_at is null
            ),
            lexical as (
              select
                id,
                row_number() over (
                  order by
                    ts_rank_cd(
                      content_tsv,
                      websearch_to_tsquery('english', :query)
                    ) desc,
                    id
                )::integer as rank
              from eligible
              where content_tsv @@ websearch_to_tsquery('english', :query)
              order by rank
              limit :candidate_limit
            ),
            semantic as (
              select
                id,
                row_number() over (
                  order by
                    embedding <=> cast(:query_embedding as vector),
                    id
                )::integer as rank
              from eligible
              order by embedding <=> cast(:query_embedding as vector), id
              limit :candidate_limit
            ),
            candidates as (
              select id from lexical
              union
              select id from semantic
            )
            select
              eligible.id,
              eligible.source_id,
              eligible.document_version_id,
              eligible.content,
              eligible.locator,
              eligible.display_name,
              lexical.rank as lexical_rank,
              semantic.rank as semantic_rank,
              (
                case when lexical.rank is null then 0
                     else 1.0 / (:rrf_k + lexical.rank) end
                +
                case when semantic.rank is null then 0
                     else 1.0 / (:rrf_k + semantic.rank) end
              ) as fused_score
            from candidates
            join eligible on eligible.id = candidates.id
            left join lexical on lexical.id = candidates.id
            left join semantic on semantic.id = candidates.id
            order by fused_score desc, eligible.id
            limit :top_k
            """
        ),
        {
            "candidate_limit": MAX_CANDIDATES_PER_PATH,
            "organization_id": organization_id,
            "query": query,
            "query_embedding": vector_literal(query_embedding),
            "rrf_k": RRF_K,
            "top_k": top_k,
            "workspace_id": workspace_id,
        },
    )
    evidence: list[EvidenceChunk] = []
    for row in result:
        evidence.append(
            EvidenceChunk(
                chunk_id=UUID(str(row.id)),
                content=str(row.content),
                fused_score=float(row.fused_score),
                lexical_rank=(
                    int(row.lexical_rank) if row.lexical_rank is not None else None
                ),
                locator=dict(row.locator),
                semantic_rank=(
                    int(row.semantic_rank) if row.semantic_rank is not None else None
                ),
                source_id=UUID(str(row.source_id)),
                source_name=str(row.display_name),
                version_id=UUID(str(row.document_version_id)),
            )
        )
    return tuple(evidence)


class RetrievalService:
    def __init__(self, embeddings: EmbeddingProvider) -> None:
        self._embeddings = embeddings

    async def retrieve(
        self,
        *,
        claims: VerifiedClaims,
        organization_id: UUID,
        workspace_id: UUID,
        query: str,
        top_k: int,
    ) -> tuple[EvidenceChunk, ...]:
        with tracer.start_as_current_span("retrieval.hybrid") as span:
            vectors = await self._embeddings.embed([query])

            async def run(session: AsyncSession) -> tuple[EvidenceChunk, ...]:
                return await hybrid_retrieve(
                    session,
                    organization_id=organization_id,
                    workspace_id=workspace_id,
                    query=query,
                    query_embedding=vectors[0],
                    top_k=top_k,
                )

            result = await with_user_database(claims, run)
            span.set_attribute("retrieval.candidate_count", len(result))
            span.set_attribute("retrieval.top_k", top_k)
            RETRIEVAL_CANDIDATES.observe(len(result))
            return result
