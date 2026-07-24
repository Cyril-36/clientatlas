# Supabase Free Project Runbook

## Live project

The ClientAtlas free project is configured in the Mumbai region.

| Setting | Value |
| --- | --- |
| Project name | `ClientAtlas` |
| Project reference | `izrishcepnwfrpracnqa` |
| Region | `ap-south-1` |
| API URL | `https://izrishcepnwfrpracnqa.supabase.co` |
| Storage bucket | `clientatlas-sources` (private) |

The public browser configuration uses the project's publishable key. Never put
a secret key, service-role key, migration credential, or database password in a
`NEXT_PUBLIC_` variable.

## Applied controls

- All migrations in `packages/database/migrations/manual` are applied in order.
- The `app` schema contains tenant-owned product tables with enabled and forced
  row-level security.
- The `clientatlas-sources` bucket is private, limited to PDF and DOCX content,
  and capped at 25 MB per object.
- pgvector is installed in the `extensions` schema.
- `clientatlas_runtime` is a non-owner `NOBYPASSRLS` login that can assume only
  the fixed `authenticated` application role.
- Migration and runtime credentials remain separate.

## Local secret files

The configured development values live only in ignored files:

- `apps/product-api/.env.local` for Next.js and browser-safe configuration.
- `.env` for the Python AI service.

Do not commit either file. Rotate the runtime database password if either file
is disclosed.

## Verification

After any database migration:

1. Run Supabase security and performance advisors.
2. Confirm every `app` table has both RLS and `FORCE ROW LEVEL SECURITY`.
3. Run the cross-tenant database integration suite with the runtime credential.
4. Test Storage read, insert, delete, and signed-URL behavior with two
   authenticated tenants.
5. Confirm the runtime role owns no application table and cannot bypass RLS.

Signed-URL tests require an authenticated worker path and must not use a
service-role client in browser or user-request modules.
