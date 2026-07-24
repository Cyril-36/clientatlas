do $$
begin
  create type app.source_kind as enum ('upload', 'google_drive');
exception
  when duplicate_object then null;
end
$$;

do $$
begin
  create type app.ingestion_state as enum (
    'queued',
    'parsing',
    'chunking',
    'embedding',
    'ready',
    'failed',
    'deleting',
    'deleted'
  );
exception
  when duplicate_object then null;
end
$$;

do $$
begin
  create type app.ingestion_job_state as enum (
    'queued',
    'running',
    'retry',
    'complete',
    'failed'
  );
exception
  when duplicate_object then null;
end
$$;

create table if not exists app.sources (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null,
  workspace_id uuid not null,
  kind app.source_kind not null,
  display_name text not null check (char_length(display_name) between 1 and 255),
  external_file_id text,
  object_path text not null check (
    object_path ~ '^[0-9a-f-]+/[0-9a-f-]+/[0-9a-f-]+/[0-9a-f-]+/[^/]+$'
  ),
  state app.ingestion_state not null default 'queued',
  active_version_id uuid,
  safe_error_code text,
  created_by uuid not null references auth.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted_at timestamptz,
  unique (organization_id, workspace_id, id),
  constraint sources_workspace_tenant_fk
    foreign key (organization_id, workspace_id)
    references app.workspaces(organization_id, id)
    on delete cascade
);

create table if not exists app.document_versions (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null,
  workspace_id uuid not null,
  source_id uuid not null,
  checksum_sha256 text not null check (checksum_sha256 ~ '^[a-f0-9]{64}$'),
  mime_type text not null check (
    mime_type in (
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
  ),
  byte_size bigint not null check (byte_size between 1 and 26214400),
  parser_version text not null,
  embedding_provider text not null,
  embedding_model text not null,
  state app.ingestion_state not null default 'queued',
  page_count integer check (page_count is null or page_count >= 1),
  chunk_count integer not null default 0 check (chunk_count >= 0),
  safe_error_code text,
  created_by uuid not null references auth.users(id),
  created_at timestamptz not null default now(),
  ready_at timestamptz,
  unique (source_id, checksum_sha256),
  unique (organization_id, workspace_id, source_id, id),
  constraint document_versions_source_tenant_fk
    foreign key (organization_id, workspace_id, source_id)
    references app.sources(organization_id, workspace_id, id)
    on delete cascade
);

alter table app.sources
  drop constraint if exists sources_active_version_tenant_fk;
alter table app.sources
  add constraint sources_active_version_tenant_fk
  foreign key (organization_id, workspace_id, id, active_version_id)
  references app.document_versions(
    organization_id,
    workspace_id,
    source_id,
    id
  );

create table if not exists app.document_chunks (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null,
  workspace_id uuid not null,
  source_id uuid not null,
  document_version_id uuid not null,
  ordinal integer not null check (ordinal >= 0),
  content text not null check (char_length(content) between 1 and 12000),
  token_count integer not null check (token_count between 1 and 4000),
  locator jsonb not null,
  content_tsv tsvector generated always as (
    to_tsvector('english', content)
  ) stored,
  embedding vector(768) not null,
  created_at timestamptz not null default now(),
  unique (document_version_id, ordinal),
  constraint document_chunks_version_tenant_fk
    foreign key (
      organization_id,
      workspace_id,
      source_id,
      document_version_id
    )
    references app.document_versions(
      organization_id,
      workspace_id,
      source_id,
      id
    )
    on delete cascade
);

create table if not exists app.ingestion_jobs (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null,
  workspace_id uuid not null,
  source_id uuid not null,
  document_version_id uuid not null,
  state app.ingestion_job_state not null default 'queued',
  attempt_count integer not null default 0 check (attempt_count between 0 and 5),
  run_after timestamptz not null default now(),
  locked_at timestamptz,
  locked_by text,
  safe_error_code text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (document_version_id),
  constraint ingestion_jobs_version_tenant_fk
    foreign key (
      organization_id,
      workspace_id,
      source_id,
      document_version_id
    )
    references app.document_versions(
      organization_id,
      workspace_id,
      source_id,
      id
    )
    on delete cascade
);

create index if not exists sources_workspace_updated_idx
  on app.sources (organization_id, workspace_id, updated_at desc)
  where deleted_at is null;
create index if not exists document_versions_source_created_idx
  on app.document_versions (source_id, created_at desc);
create index if not exists document_chunks_tsv_idx
  on app.document_chunks using gin (content_tsv);
create index if not exists document_chunks_tenant_idx
  on app.document_chunks (
    organization_id,
    workspace_id,
    source_id,
    document_version_id
  );
create index if not exists document_chunks_embedding_hnsw_idx
  on app.document_chunks using hnsw (embedding vector_cosine_ops);
create index if not exists ingestion_jobs_claim_idx
  on app.ingestion_jobs (state, run_after, created_at)
  where state in ('queued', 'retry');

revoke all on app.sources from public;
revoke all on app.document_versions from public;
revoke all on app.document_chunks from public;
revoke all on app.ingestion_jobs from public;

grant select, insert, update, delete on app.sources to authenticated;
grant select, insert, update, delete on app.document_versions to authenticated;
grant select, insert, update, delete on app.document_chunks to authenticated;
grant select, insert, update, delete on app.ingestion_jobs to authenticated;

alter table app.sources enable row level security;
alter table app.sources force row level security;
alter table app.document_versions enable row level security;
alter table app.document_versions force row level security;
alter table app.document_chunks enable row level security;
alter table app.document_chunks force row level security;
alter table app.ingestion_jobs enable row level security;
alter table app.ingestion_jobs force row level security;

drop policy if exists sources_read on app.sources;
create policy sources_read on app.sources
  for select to authenticated
  using (app.is_organization_member(organization_id));
drop policy if exists sources_insert on app.sources;
create policy sources_insert on app.sources
  for insert to authenticated
  with check (
    created_by = auth.uid()
    and app.organization_role_for(organization_id) in (
      'owner'::app.organization_role,
      'admin'::app.organization_role,
      'editor'::app.organization_role
    )
  );
drop policy if exists sources_update on app.sources;
create policy sources_update on app.sources
  for update to authenticated
  using (
    app.organization_role_for(organization_id) in (
      'owner'::app.organization_role,
      'admin'::app.organization_role,
      'editor'::app.organization_role
    )
  )
  with check (
    app.organization_role_for(organization_id) in (
      'owner'::app.organization_role,
      'admin'::app.organization_role,
      'editor'::app.organization_role
    )
  );
drop policy if exists sources_delete on app.sources;
create policy sources_delete on app.sources
  for delete to authenticated
  using (
    app.organization_role_for(organization_id) in (
      'owner'::app.organization_role,
      'admin'::app.organization_role,
      'editor'::app.organization_role
    )
  );

drop policy if exists document_versions_read on app.document_versions;
create policy document_versions_read on app.document_versions
  for select to authenticated
  using (app.is_organization_member(organization_id));
drop policy if exists document_versions_insert on app.document_versions;
create policy document_versions_insert on app.document_versions
  for insert to authenticated
  with check (
    created_by = auth.uid()
    and app.organization_role_for(organization_id) in (
      'owner'::app.organization_role,
      'admin'::app.organization_role,
      'editor'::app.organization_role
    )
  );
drop policy if exists document_versions_update on app.document_versions;
create policy document_versions_update on app.document_versions
  for update to authenticated
  using (
    app.organization_role_for(organization_id) in (
      'owner'::app.organization_role,
      'admin'::app.organization_role,
      'editor'::app.organization_role
    )
  )
  with check (
    app.organization_role_for(organization_id) in (
      'owner'::app.organization_role,
      'admin'::app.organization_role,
      'editor'::app.organization_role
    )
  );
drop policy if exists document_versions_delete on app.document_versions;
create policy document_versions_delete on app.document_versions
  for delete to authenticated
  using (
    app.organization_role_for(organization_id) in (
      'owner'::app.organization_role,
      'admin'::app.organization_role,
      'editor'::app.organization_role
    )
  );

drop policy if exists document_chunks_read on app.document_chunks;
create policy document_chunks_read on app.document_chunks
  for select to authenticated
  using (app.is_organization_member(organization_id));
drop policy if exists document_chunks_write on app.document_chunks;
create policy document_chunks_write on app.document_chunks
  for all to authenticated
  using (
    app.organization_role_for(organization_id) in (
      'owner'::app.organization_role,
      'admin'::app.organization_role,
      'editor'::app.organization_role
    )
  )
  with check (
    app.organization_role_for(organization_id) in (
      'owner'::app.organization_role,
      'admin'::app.organization_role,
      'editor'::app.organization_role
    )
  );

drop policy if exists ingestion_jobs_read on app.ingestion_jobs;
create policy ingestion_jobs_read on app.ingestion_jobs
  for select to authenticated
  using (app.is_organization_member(organization_id));
drop policy if exists ingestion_jobs_write on app.ingestion_jobs;
create policy ingestion_jobs_write on app.ingestion_jobs
  for all to authenticated
  using (
    app.organization_role_for(organization_id) in (
      'owner'::app.organization_role,
      'admin'::app.organization_role,
      'editor'::app.organization_role
    )
  )
  with check (
    app.organization_role_for(organization_id) in (
      'owner'::app.organization_role,
      'admin'::app.organization_role,
      'editor'::app.organization_role
    )
  );
