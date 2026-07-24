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
    row_value.id,
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

drop trigger if exists audit_workspace_changes on app.workspaces;
create trigger audit_workspace_changes
after insert or update or delete on app.workspaces
for each row execute function app.audit_workspace_change();

revoke all on function app.audit_workspace_change() from public;
revoke all on function app.audit_workspace_change() from authenticated;
