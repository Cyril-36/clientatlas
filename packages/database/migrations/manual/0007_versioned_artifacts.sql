do $$
begin
  create type app.artifact_type as enum (
    'onboarding_brief',
    'readiness_report',
    'action_plan'
  );
exception
  when duplicate_object then null;
end
$$;

do $$
begin
  create type app.artifact_status as enum (
    'draft',
    'reviewed',
    'approved',
    'archived'
  );
exception
  when duplicate_object then null;
end
$$;

create table if not exists app.artifacts (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null,
  workspace_id uuid not null,
  type app.artifact_type not null,
  title text not null check (char_length(title) between 1 and 200),
  status app.artifact_status not null default 'draft',
  current_version_id uuid,
  created_by uuid not null references auth.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (organization_id, workspace_id, id),
  constraint artifacts_workspace_tenant_fk
    foreign key (organization_id, workspace_id)
    references app.workspaces(organization_id, id)
    on delete cascade
);

create table if not exists app.artifact_versions (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null,
  workspace_id uuid not null,
  artifact_id uuid not null,
  version_number integer not null check (version_number >= 1),
  schema_version text not null,
  content jsonb not null,
  created_by uuid not null references auth.users(id),
  created_at timestamptz not null default now(),
  unique (artifact_id, version_number),
  unique (organization_id, workspace_id, artifact_id, id),
  constraint artifact_versions_artifact_tenant_fk
    foreign key (organization_id, workspace_id, artifact_id)
    references app.artifacts(organization_id, workspace_id, id)
    on delete cascade
);

alter table app.artifacts
  drop constraint if exists artifacts_current_version_tenant_fk;
alter table app.artifacts
  add constraint artifacts_current_version_tenant_fk
  foreign key (organization_id, workspace_id, id, current_version_id)
  references app.artifact_versions(
    organization_id,
    workspace_id,
    artifact_id,
    id
  );

create table if not exists app.artifact_evidence (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null,
  workspace_id uuid not null,
  artifact_id uuid not null,
  artifact_version_id uuid not null,
  json_pointer text not null check (
    json_pointer ~ '^/(?:[^~/]|~0|~1)*(?:/(?:[^~/]|~0|~1)*)*$'
  ),
  chunk_id uuid references app.document_chunks(id) on delete set null,
  source_id uuid not null,
  document_version_id uuid not null,
  state text not null default 'active'
    check (state in ('active', 'missing', 'superseded')),
  created_at timestamptz not null default now(),
  unique (artifact_version_id, json_pointer, chunk_id),
  constraint artifact_evidence_version_tenant_fk
    foreign key (
      organization_id,
      workspace_id,
      artifact_id,
      artifact_version_id
    )
    references app.artifact_versions(
      organization_id,
      workspace_id,
      artifact_id,
      id
    )
    on delete cascade
);

create index if not exists artifacts_workspace_updated_idx
  on app.artifacts (organization_id, workspace_id, updated_at desc);
create index if not exists artifact_versions_artifact_version_idx
  on app.artifact_versions (artifact_id, version_number desc);
create index if not exists artifact_evidence_source_idx
  on app.artifact_evidence (source_id, state);

revoke all on app.artifacts from public;
revoke all on app.artifact_versions from public;
revoke all on app.artifact_evidence from public;
grant select, insert, update, delete on app.artifacts to authenticated;
grant select, insert on app.artifact_versions to authenticated;
grant select, insert, update on app.artifact_evidence to authenticated;

alter table app.artifacts enable row level security;
alter table app.artifacts force row level security;
alter table app.artifact_versions enable row level security;
alter table app.artifact_versions force row level security;
alter table app.artifact_evidence enable row level security;
alter table app.artifact_evidence force row level security;

drop policy if exists artifacts_member_read on app.artifacts;
create policy artifacts_member_read on app.artifacts
  for select to authenticated
  using (app.is_organization_member(organization_id));
drop policy if exists artifacts_editor_insert on app.artifacts;
create policy artifacts_editor_insert on app.artifacts
  for insert to authenticated
  with check (
    created_by = auth.uid()
    and app.organization_role_for(organization_id) in (
      'owner'::app.organization_role,
      'admin'::app.organization_role,
      'editor'::app.organization_role
    )
  );
drop policy if exists artifacts_editor_update on app.artifacts;
create policy artifacts_editor_update on app.artifacts
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

drop policy if exists artifact_versions_member_read on app.artifact_versions;
create policy artifact_versions_member_read on app.artifact_versions
  for select to authenticated
  using (app.is_organization_member(organization_id));
drop policy if exists artifact_versions_editor_insert on app.artifact_versions;
create policy artifact_versions_editor_insert on app.artifact_versions
  for insert to authenticated
  with check (
    created_by = auth.uid()
    and app.organization_role_for(organization_id) in (
      'owner'::app.organization_role,
      'admin'::app.organization_role,
      'editor'::app.organization_role
    )
  );

drop policy if exists artifact_evidence_member_read on app.artifact_evidence;
create policy artifact_evidence_member_read on app.artifact_evidence
  for select to authenticated
  using (app.is_organization_member(organization_id));
drop policy if exists artifact_evidence_editor_insert on app.artifact_evidence;
create policy artifact_evidence_editor_insert on app.artifact_evidence
  for insert to authenticated
  with check (
    app.organization_role_for(organization_id) in (
      'owner'::app.organization_role,
      'admin'::app.organization_role,
      'editor'::app.organization_role
    )
  );
drop policy if exists artifact_evidence_editor_update on app.artifact_evidence;
create policy artifact_evidence_editor_update on app.artifact_evidence
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
