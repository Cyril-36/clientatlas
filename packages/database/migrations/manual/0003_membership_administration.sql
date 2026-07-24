create or replace function app.set_organization_membership(
  target_organization_id uuid,
  target_user_id uuid,
  target_role app.organization_role
)
returns app.organization_memberships
language plpgsql
security definer
set search_path = ''
as $$
declare
  actor_id uuid := auth.uid();
  actor_role app.organization_role;
  result app.organization_memberships;
begin
  actor_role := app.organization_role_for(target_organization_id);
  if actor_id is null or actor_role not in (
    'owner'::app.organization_role,
    'admin'::app.organization_role
  ) then
    raise exception using errcode = '42501', message = 'membership_manage_forbidden';
  end if;

  if target_role = 'owner'::app.organization_role
     and actor_role <> 'owner'::app.organization_role then
    raise exception using errcode = '42501', message = 'owner_role_requires_owner';
  end if;

  insert into app.organization_memberships (
    organization_id,
    user_id,
    role,
    invited_by
  )
  values (
    target_organization_id,
    target_user_id,
    target_role,
    actor_id
  )
  on conflict (organization_id, user_id)
  do update set
    role = excluded.role,
    updated_at = now()
  returning * into result;

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
    target_organization_id,
    actor_id,
    'user',
    'membership.set',
    'user',
    target_user_id,
    jsonb_build_object('role', target_role::text)
  );

  return result;
end;
$$;

create or replace function app.remove_organization_membership(
  target_organization_id uuid,
  target_user_id uuid
)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  actor_id uuid := auth.uid();
  actor_role app.organization_role;
  target_existing_role app.organization_role;
  owner_count integer;
begin
  actor_role := app.organization_role_for(target_organization_id);
  if actor_id is null or actor_role not in (
    'owner'::app.organization_role,
    'admin'::app.organization_role
  ) then
    raise exception using errcode = '42501', message = 'membership_manage_forbidden';
  end if;

  select role into target_existing_role
  from app.organization_memberships
  where organization_id = target_organization_id
    and user_id = target_user_id
  for update;

  if target_existing_role is null then
    return false;
  end if;

  if target_existing_role = 'owner'::app.organization_role then
    if actor_role <> 'owner'::app.organization_role then
      raise exception using errcode = '42501', message = 'owner_role_requires_owner';
    end if;

    select count(*) into owner_count
    from app.organization_memberships
    where organization_id = target_organization_id
      and role = 'owner'::app.organization_role;

    if owner_count <= 1 then
      raise exception using errcode = '23514', message = 'last_owner_required';
    end if;
  end if;

  delete from app.organization_memberships
  where organization_id = target_organization_id
    and user_id = target_user_id;

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
    target_organization_id,
    actor_id,
    'user',
    'membership.removed',
    'user',
    target_user_id,
    '{}'::jsonb
  );

  return true;
end;
$$;

revoke all on function app.set_organization_membership(
  uuid,
  uuid,
  app.organization_role
) from public;
revoke all on function app.remove_organization_membership(uuid, uuid) from public;

grant execute on function app.set_organization_membership(
  uuid,
  uuid,
  app.organization_role
) to authenticated;
grant execute on function app.remove_organization_membership(uuid, uuid)
  to authenticated;
