do $$
begin
  if to_regclass('storage.buckets') is null
     or to_regclass('storage.objects') is null then
    raise notice 'Supabase Storage schema absent; skipping Storage policies';
    return;
  end if;

  insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
  values (
    'clientatlas-sources',
    'clientatlas-sources',
    false,
    26214400,
    array[
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]
  )
  on conflict (id) do update set
    public = false,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

  execute 'drop policy if exists clientatlas_sources_read on storage.objects';
  execute $policy$
    create policy clientatlas_sources_read on storage.objects
      for select to authenticated
      using (
        bucket_id = 'clientatlas-sources'
        and app.is_organization_member(
          ((storage.foldername(name))[1])::uuid
        )
      )
  $policy$;

  execute 'drop policy if exists clientatlas_sources_insert on storage.objects';
  execute $policy$
    create policy clientatlas_sources_insert on storage.objects
      for insert to authenticated
      with check (
        bucket_id = 'clientatlas-sources'
        and app.organization_role_for(
          ((storage.foldername(name))[1])::uuid
        ) in (
          'owner'::app.organization_role,
          'admin'::app.organization_role,
          'editor'::app.organization_role
        )
      )
  $policy$;

  execute 'drop policy if exists clientatlas_sources_delete on storage.objects';
  execute $policy$
    create policy clientatlas_sources_delete on storage.objects
      for delete to authenticated
      using (
        bucket_id = 'clientatlas-sources'
        and app.organization_role_for(
          ((storage.foldername(name))[1])::uuid
        ) in (
          'owner'::app.organization_role,
          'admin'::app.organization_role,
          'editor'::app.organization_role
        )
      )
  $policy$;
end
$$;
