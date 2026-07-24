create or replace function app.audit_workspace_change()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  row_value app.workspaces;
begin
  row_value := case when tg_op = 'DELETE' then old else new end;

  if tg_op = 'DELETE' and not exists (
    select 1
    from app.organizations organization
    where organization.id = row_value.organization_id
  ) then
    return old;
  end if;

  insert into app.audit_events (
    organization_id,
    workspace_id,
    actor_user_id,
    actor_type,
    event_type,
    target_type,
    target_id,
    safe_details
  )
  values (
    row_value.organization_id,
    case when tg_op = 'DELETE' then null else row_value.id end,
    auth.uid(),
    'user',
    case tg_op
      when 'INSERT' then 'workspace.created'
      when 'UPDATE' then 'workspace.updated'
      else 'workspace.deleted'
    end,
    'workspace',
    row_value.id,
    '{}'::jsonb
  );
  return case when tg_op = 'DELETE' then old else new end;
end;
$$;
