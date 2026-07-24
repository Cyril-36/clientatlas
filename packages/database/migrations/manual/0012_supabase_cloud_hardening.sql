create schema if not exists extensions;

do $$
begin
  if exists (
    select 1
    from pg_extension extension
    join pg_namespace namespace on namespace.oid = extension.extnamespace
    where extension.extname = 'vector'
      and namespace.nspname <> 'extensions'
  ) then
    alter extension vector set schema extensions;
  end if;
end
$$;

do $$
begin
  create role clientatlas_runtime
    login
    noinherit;
exception
  when duplicate_object then null;
end
$$;

alter role clientatlas_runtime
  login
  noinherit;

do $$
begin
  if exists (
    select 1
    from pg_roles
    where rolname = 'clientatlas_runtime'
      and (
        rolsuper
        or rolcreatedb
        or rolcreaterole
        or rolreplication
        or rolbypassrls
      )
  ) then
    raise exception 'clientatlas_runtime has privileged role attributes';
  end if;
end
$$;

alter role clientatlas_runtime
  set search_path = "$user", public, extensions;

grant authenticated to clientatlas_runtime;
revoke all on schema private from clientatlas_runtime;
