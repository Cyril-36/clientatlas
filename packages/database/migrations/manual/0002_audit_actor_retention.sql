alter table app.audit_events
  drop constraint if exists audit_events_actor_user_id_fkey;

alter table app.audit_events
  add constraint audit_events_actor_user_id_fkey
  foreign key (actor_user_id)
  references auth.users(id)
  on delete set null;

