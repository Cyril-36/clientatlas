create extension if not exists vector;

create schema if not exists app;

do $$
begin
  create type app.organization_role as enum (
    'owner',
    'admin',
    'editor',
    'viewer'
  );
exception
  when duplicate_object then null;
end
$$;

create table if not exists app.organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null check (char_length(name) between 1 and 120),
  slug text not null unique
    check (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$')
    check (char_length(slug) between 3 and 80),
  created_by uuid not null references auth.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists app.organization_memberships (
  organization_id uuid not null references app.organizations(id)
    on delete cascade,
  user_id uuid not null references auth.users(id),
  role app.organization_role not null,
  invited_by uuid references auth.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint organization_memberships_pkey
    primary key (organization_id, user_id)
);

create index if not exists organization_memberships_user_org_idx
  on app.organization_memberships (user_id, organization_id);

create table if not exists app.workspaces (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references app.organizations(id)
    on delete cascade,
  name text not null check (char_length(name) between 1 and 120),
  description text check (
    description is null or char_length(description) <= 2000
  ),
  privacy_mode text not null default 'local_confidential'
    check (privacy_mode in ('local_confidential', 'synthetic_demo')),
  created_by uuid not null references auth.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (organization_id, id)
);

create index if not exists workspaces_org_updated_idx
  on app.workspaces (organization_id, updated_at desc);

create table if not exists app.audit_events (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid references app.organizations(id) on delete set null,
  workspace_id uuid,
  actor_user_id uuid references auth.users(id),
  actor_type text not null check (
    actor_type in ('user', 'worker', 'system')
  ),
  event_type text not null check (char_length(event_type) between 1 and 100),
  target_type text not null check (char_length(target_type) between 1 and 100),
  target_id uuid,
  safe_details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint audit_events_workspace_tenant_fk
    foreign key (organization_id, workspace_id)
    references app.workspaces(organization_id, id)
);

create index if not exists audit_events_org_created_idx
  on app.audit_events (organization_id, created_at desc);

create or replace function app.is_organization_member(
  target_organization_id uuid
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from app.organization_memberships membership
    where membership.organization_id = target_organization_id
      and membership.user_id = auth.uid()
  );
$$;

create or replace function app.organization_role_for(
  target_organization_id uuid
)
returns app.organization_role
language sql
stable
security definer
set search_path = ''
as $$
  select membership.role
  from app.organization_memberships membership
  where membership.organization_id = target_organization_id
    and membership.user_id = auth.uid()
  limit 1;
$$;

create or replace function app.create_organization(
  organization_name text,
  organization_slug text
)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  actor_id uuid := auth.uid();
  organization_id uuid := gen_random_uuid();
begin
  if actor_id is null then
    raise exception using errcode = '28000', message = 'authentication_required';
  end if;

  if char_length(organization_name) not between 1 and 120 then
    raise exception using errcode = '22023', message = 'invalid_organization_name';
  end if;

  if char_length(organization_slug) not between 3 and 80
     or organization_slug !~ '^[a-z0-9]+(?:-[a-z0-9]+)*$' then
    raise exception using errcode = '22023', message = 'invalid_organization_slug';
  end if;

  insert into app.organizations (
    id,
    name,
    slug,
    created_by
  )
  values (
    organization_id,
    organization_name,
    organization_slug,
    actor_id
  );

  insert into app.organization_memberships (
    organization_id,
    user_id,
    role
  )
  values (
    organization_id,
    actor_id,
    'owner'::app.organization_role
  );

  insert into app.audit_events (
    organization_id,
    actor_user_id,
    actor_type,
    event_type,
    target_type,
    target_id,
    safe_details
  )
  values (
    organization_id,
    actor_id,
    'user',
    'organization.created',
    'organization',
    organization_id,
    '{}'::jsonb
  );

  return organization_id;
end;
$$;

revoke all on schema app from public;
revoke all on all tables in schema app from public;
revoke all on all functions in schema app from public;

grant usage on schema app to authenticated;
grant select, update, delete on app.organizations to authenticated;
grant select on app.organization_memberships to authenticated;
grant select, insert, update, delete on app.workspaces to authenticated;
grant select on app.audit_events to authenticated;
grant execute on function app.is_organization_member(uuid) to authenticated;
grant execute on function app.organization_role_for(uuid) to authenticated;
grant execute on function app.create_organization(text, text) to authenticated;

alter table app.organizations enable row level security;
alter table app.organizations force row level security;
alter table app.organization_memberships enable row level security;
alter table app.organization_memberships force row level security;
alter table app.workspaces enable row level security;
alter table app.workspaces force row level security;
alter table app.audit_events enable row level security;
alter table app.audit_events force row level security;

drop policy if exists organizations_read on app.organizations;
create policy organizations_read
  on app.organizations
  for select
  to authenticated
  using (app.is_organization_member(id));

drop policy if exists organizations_update on app.organizations;
create policy organizations_update
  on app.organizations
  for update
  to authenticated
  using (
    app.organization_role_for(id) in (
      'owner'::app.organization_role,
      'admin'::app.organization_role
    )
  )
  with check (
    app.organization_role_for(id) in (
      'owner'::app.organization_role,
      'admin'::app.organization_role
    )
  );

drop policy if exists organizations_delete on app.organizations;
create policy organizations_delete
  on app.organizations
  for delete
  to authenticated
  using (
    app.organization_role_for(id) = 'owner'::app.organization_role
  );

drop policy if exists memberships_read on app.organization_memberships;
create policy memberships_read
  on app.organization_memberships
  for select
  to authenticated
  using (app.is_organization_member(organization_id));

drop policy if exists workspaces_read on app.workspaces;
create policy workspaces_read
  on app.workspaces
  for select
  to authenticated
  using (app.is_organization_member(organization_id));

drop policy if exists workspaces_insert on app.workspaces;
create policy workspaces_insert
  on app.workspaces
  for insert
  to authenticated
  with check (
    created_by = auth.uid()
    and app.organization_role_for(organization_id) in (
      'owner'::app.organization_role,
      'admin'::app.organization_role,
      'editor'::app.organization_role
    )
  );

drop policy if exists workspaces_update on app.workspaces;
create policy workspaces_update
  on app.workspaces
  for update
  to authenticated
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

drop policy if exists workspaces_delete on app.workspaces;
create policy workspaces_delete
  on app.workspaces
  for delete
  to authenticated
  using (
    app.organization_role_for(organization_id) in (
      'owner'::app.organization_role,
      'admin'::app.organization_role
    )
  );

drop policy if exists audit_events_read on app.audit_events;
create policy audit_events_read
  on app.audit_events
  for select
  to authenticated
  using (
    organization_id is not null
    and app.organization_role_for(organization_id) in (
      'owner'::app.organization_role,
      'admin'::app.organization_role
    )
  );
