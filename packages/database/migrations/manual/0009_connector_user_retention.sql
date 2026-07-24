alter table private.google_drive_oauth_states
  drop constraint if exists google_drive_oauth_states_user_id_fkey;
alter table private.google_drive_oauth_states
  add constraint google_drive_oauth_states_user_id_fkey
  foreign key (user_id) references auth.users(id) on delete cascade;

alter table app.google_drive_connections
  drop constraint if exists google_drive_connections_user_id_fkey;
alter table app.google_drive_connections
  add constraint google_drive_connections_user_id_fkey
  foreign key (user_id) references auth.users(id) on delete cascade;
