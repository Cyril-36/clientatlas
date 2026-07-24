create schema if not exists auth;

create table if not exists auth.users (
  id uuid primary key,
  email text unique,
  created_at timestamptz not null default now()
);

do $$
begin
  create role authenticated nologin noinherit nobypassrls;
exception
  when duplicate_object then null;
end
$$;

do $$
begin
  create role clientatlas_runtime
    login
    password 'local-runtime-only'
    noinherit
    nobypassrls;
exception
  when duplicate_object then null;
end
$$;

grant authenticated to clientatlas_runtime;

create or replace function auth.jwt()
returns jsonb
language sql
stable
as $$
  select coalesce(
    nullif(current_setting('request.jwt.claims', true), ''),
    '{}'
  )::jsonb;
$$;

create or replace function auth.uid()
returns uuid
language sql
stable
as $$
  select nullif(auth.jwt() ->> 'sub', '')::uuid;
$$;

grant usage on schema auth to authenticated;
grant execute on function auth.jwt() to authenticated;
grant execute on function auth.uid() to authenticated;
