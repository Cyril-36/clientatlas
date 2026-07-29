-- MiniLM emits 384-dimensional vectors. Existing vectors came from a
-- different embedding space and cannot be converted truthfully. Invalidate
-- only derived chunks; retained source objects can be re-indexed.

update app.artifact_evidence
set state = 'missing',
    chunk_id = null
where chunk_id is not null;

delete from app.document_chunks;

drop index if exists app.document_chunks_embedding_hnsw_idx;

alter table app.document_chunks
  drop column embedding;

alter table app.document_chunks
  add column embedding extensions.vector(384) not null;

create index document_chunks_embedding_hnsw_idx
  on app.document_chunks using hnsw (embedding extensions.vector_cosine_ops);

with latest_versions as (
  select distinct on (source_id)
    id,
    source_id
  from app.document_versions
  where state <> 'deleted'
  order by source_id, created_at desc, id desc
)
update app.document_versions version
set state = cast(
      case
        when version.id = latest.id then 'queued'
        else 'failed'
      end
      as app.ingestion_state
    ),
    chunk_count = 0,
    page_count = null,
    embedding_provider = 'huggingface',
    embedding_model = 'sentence-transformers/all-MiniLM-L6-v2',
    safe_error_code = case
      when version.id = latest.id then null
      else 'superseded_embedding_model'
    end,
    ready_at = null
from latest_versions latest
where version.source_id = latest.source_id
  and version.state <> 'deleted';

update app.sources
set state = 'queued',
    active_version_id = null,
    safe_error_code = null,
    updated_at = now()
where deleted_at is null;

update app.ingestion_jobs
set state = 'queued',
    attempt_count = 0,
    run_after = now(),
    locked_at = null,
    locked_by = null,
    safe_error_code = null,
    updated_at = now()
where document_version_id in (
  select id
  from app.document_versions
  where state = 'queued'
);
