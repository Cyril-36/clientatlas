create schema if not exists private;
revoke all on schema private from public;
revoke all on schema private from authenticated;

create table if not exists app.google_drive_connections (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null,
  workspace_id uuid not null,
  user_id uuid not null references auth.users(id),
  google_subject text not null,
  granted_scopes text[] not null,
  status text not null default 'active'
    check (status in ('active', 'revoked')),
  connected_at timestamptz not null default now(),
  revoked_at timestamptz,
  unique (organization_id, workspace_id, user_id),
  unique (organization_id, workspace_id, id),
  constraint google_drive_connections_workspace_tenant_fk
    foreign key (organization_id, workspace_id)
    references app.workspaces(organization_id, id)
    on delete cascade
);

create table if not exists private.google_drive_credentials (
  connection_id uuid primary key
    references app.google_drive_connections(id) on delete cascade,
  encrypted_refresh_token bytea not null,
  updated_at timestamptz not null default now()
);

create table if not exists private.google_drive_oauth_states (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null,
  workspace_id uuid not null,
  user_id uuid not null references auth.users(id),
  state_hash text not null unique check (state_hash ~ '^[a-f0-9]{64}$'),
  encrypted_pkce_verifier bytea not null,
  expires_at timestamptz not null,
  consumed_at timestamptz,
  created_at timestamptz not null default now()
);

revoke all on private.google_drive_credentials from public;
revoke all on private.google_drive_oauth_states from public;
revoke all on private.google_drive_credentials from authenticated;
revoke all on private.google_drive_oauth_states from authenticated;

grant select on app.google_drive_connections to authenticated;
alter table app.google_drive_connections enable row level security;
alter table app.google_drive_connections force row level security;
drop policy if exists google_drive_connections_own_read
  on app.google_drive_connections;
create policy google_drive_connections_own_read
  on app.google_drive_connections
  for select to authenticated
  using (
    user_id = auth.uid()
    and app.is_organization_member(organization_id)
  );

create or replace function app.begin_google_drive_oauth(
  target_organization_id uuid,
  target_workspace_id uuid,
  target_state_hash text,
  target_encrypted_pkce_verifier bytea,
  target_expires_at timestamptz
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  actor_id uuid := auth.uid();
begin
  if actor_id is null
     or app.organization_role_for(target_organization_id) not in (
       'owner'::app.organization_role,
       'admin'::app.organization_role,
       'editor'::app.organization_role
     )
     or not exists (
       select 1 from app.workspaces
       where organization_id = target_organization_id
         and id = target_workspace_id
     ) then
    raise exception using errcode = '42501', message = 'connector_forbidden';
  end if;

  delete from private.google_drive_oauth_states
  where user_id = actor_id
    and (expires_at < now() or consumed_at is not null);

  insert into private.google_drive_oauth_states (
    organization_id,
    workspace_id,
    user_id,
    state_hash,
    encrypted_pkce_verifier,
    expires_at
  )
  values (
    target_organization_id,
    target_workspace_id,
    actor_id,
    target_state_hash,
    target_encrypted_pkce_verifier,
    target_expires_at
  );
end;
$$;

create or replace function app.consume_google_drive_oauth(
  target_state_hash text
)
returns table (
  organization_id uuid,
  workspace_id uuid,
  encrypted_pkce_verifier bytea
)
language plpgsql
security definer
set search_path = ''
as $$
begin
  return query
  update private.google_drive_oauth_states state
  set consumed_at = now()
  where state.state_hash = target_state_hash
    and state.user_id = auth.uid()
    and state.consumed_at is null
    and state.expires_at > now()
  returning
    state.organization_id,
    state.workspace_id,
    state.encrypted_pkce_verifier;
end;
$$;

create or replace function app.save_google_drive_connection(
  target_organization_id uuid,
  target_workspace_id uuid,
  target_google_subject text,
  target_granted_scopes text[],
  target_encrypted_refresh_token bytea
)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  actor_id uuid := auth.uid();
  connection_id uuid;
begin
  if actor_id is null
     or app.organization_role_for(target_organization_id) not in (
       'owner'::app.organization_role,
       'admin'::app.organization_role,
       'editor'::app.organization_role
     ) then
    raise exception using errcode = '42501', message = 'connector_forbidden';
  end if;

  insert into app.google_drive_connections (
    organization_id,
    workspace_id,
    user_id,
    google_subject,
    granted_scopes,
    status,
    revoked_at
  )
  values (
    target_organization_id,
    target_workspace_id,
    actor_id,
    target_google_subject,
    target_granted_scopes,
    'active',
    null
  )
  on conflict (organization_id, workspace_id, user_id)
  do update set
    google_subject = excluded.google_subject,
    granted_scopes = excluded.granted_scopes,
    status = 'active',
    revoked_at = null,
    connected_at = now()
  returning id into connection_id;

  insert into private.google_drive_credentials (
    connection_id,
    encrypted_refresh_token
  )
  values (connection_id, target_encrypted_refresh_token)
  on conflict (connection_id)
  do update set
    encrypted_refresh_token = excluded.encrypted_refresh_token,
    updated_at = now();

  return connection_id;
end;
$$;

create or replace function app.get_google_drive_credential(
  target_organization_id uuid,
  target_workspace_id uuid
)
returns table (
  connection_id uuid,
  google_subject text,
  granted_scopes text[],
  encrypted_refresh_token bytea
)
language sql
stable
security definer
set search_path = ''
as $$
  select
    connection.id,
    connection.google_subject,
    connection.granted_scopes,
    credential.encrypted_refresh_token
  from app.google_drive_connections connection
  join private.google_drive_credentials credential
    on credential.connection_id = connection.id
  where connection.organization_id = target_organization_id
    and connection.workspace_id = target_workspace_id
    and connection.user_id = auth.uid()
    and connection.status = 'active'
    and app.is_organization_member(connection.organization_id)
  limit 1;
$$;

create or replace function app.revoke_google_drive_connection(
  target_organization_id uuid,
  target_workspace_id uuid
)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  target_connection_id uuid;
begin
  select id into target_connection_id
  from app.google_drive_connections
  where organization_id = target_organization_id
    and workspace_id = target_workspace_id
    and user_id = auth.uid()
    and status = 'active'
  for update;

  if target_connection_id is null then
    return false;
  end if;
  delete from private.google_drive_credentials
  where connection_id = target_connection_id;
  update app.google_drive_connections
  set status = 'revoked', revoked_at = now()
  where id = target_connection_id;
  return true;
end;
$$;

revoke all on function app.begin_google_drive_oauth(
  uuid, uuid, text, bytea, timestamptz
) from public;
revoke all on function app.consume_google_drive_oauth(text) from public;
revoke all on function app.save_google_drive_connection(
  uuid, uuid, text, text[], bytea
) from public;
revoke all on function app.get_google_drive_credential(uuid, uuid) from public;
revoke all on function app.revoke_google_drive_connection(uuid, uuid) from public;

grant execute on function app.begin_google_drive_oauth(
  uuid, uuid, text, bytea, timestamptz
) to authenticated;
grant execute on function app.consume_google_drive_oauth(text) to authenticated;
grant execute on function app.save_google_drive_connection(
  uuid, uuid, text, text[], bytea
) to authenticated;
grant execute on function app.get_google_drive_credential(uuid, uuid)
  to authenticated;
grant execute on function app.revoke_google_drive_connection(uuid, uuid)
  to authenticated;
