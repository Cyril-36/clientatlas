create table if not exists app.conversations (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null,
  workspace_id uuid not null,
  title text not null check (char_length(title) between 1 and 200),
  created_by uuid not null references auth.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (organization_id, workspace_id, id),
  constraint conversations_workspace_tenant_fk
    foreign key (organization_id, workspace_id)
    references app.workspaces(organization_id, id)
    on delete cascade
);

create table if not exists app.messages (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null,
  workspace_id uuid not null,
  conversation_id uuid not null,
  role text not null check (role in ('user', 'assistant')),
  content text not null check (char_length(content) between 1 and 50000),
  content_format text not null default 'plain_text'
    check (content_format = 'plain_text'),
  citations jsonb not null default '[]'::jsonb,
  abstained boolean not null default false,
  provider text,
  model text,
  created_by uuid not null references auth.users(id),
  created_at timestamptz not null default now(),
  unique (organization_id, workspace_id, conversation_id, id),
  constraint messages_conversation_tenant_fk
    foreign key (organization_id, workspace_id, conversation_id)
    references app.conversations(organization_id, workspace_id, id)
    on delete cascade
);

create index if not exists conversations_user_updated_idx
  on app.conversations (created_by, updated_at desc);
create index if not exists messages_conversation_created_idx
  on app.messages (conversation_id, created_at);

revoke all on app.conversations from public;
revoke all on app.messages from public;
grant select, insert, update, delete on app.conversations to authenticated;
grant select, insert, update, delete on app.messages to authenticated;

alter table app.conversations enable row level security;
alter table app.conversations force row level security;
alter table app.messages enable row level security;
alter table app.messages force row level security;

drop policy if exists conversations_own on app.conversations;
create policy conversations_own on app.conversations
  for all to authenticated
  using (
    created_by = auth.uid()
    and app.is_organization_member(organization_id)
  )
  with check (
    created_by = auth.uid()
    and app.is_organization_member(organization_id)
  );

drop policy if exists messages_own on app.messages;
create policy messages_own on app.messages
  for all to authenticated
  using (
    created_by = auth.uid()
    and exists (
      select 1
      from app.conversations conversation
      where conversation.id = messages.conversation_id
        and conversation.created_by = auth.uid()
    )
  )
  with check (
    created_by = auth.uid()
    and exists (
      select 1
      from app.conversations conversation
      where conversation.id = messages.conversation_id
        and conversation.created_by = auth.uid()
    )
  );
