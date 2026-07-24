# ClientAtlas V1 Implementation Status

Status date: 2026-07-24

## Implemented and locally verified

- Headless organization, workspace, and membership APIs.
- Strict Supabase JWT validation in TypeScript and Python.
- Transaction-local claims, fixed role switching, forced RLS, and
  pooled-context leakage tests.
- PDF/DOCX validation, parsing, deterministic chunking, local storage,
  ingestion states, bounded retry state, re-indexing, and active-data deletion.
- Generated Supabase Storage policies with narrow object-path authorization.
- PostgreSQL full-text plus pgvector retrieval with RRF.
- Ollama generation and embedding adapters.
- Synthetic-only Gemini adapter with server-side privacy routing.
- Validated citations, abstention, plain-text SSE, and message persistence.
- Versioned onboarding brief, readiness report, and action-plan schemas.
- Artifact editing, immutable history, evidence pointers, and deletion flags.
- Google Drive `drive.file` OAuth with PKCE, one-use state, encrypted refresh
  tokens, import, and revocation.
- Thirty-case synthetic evaluation dataset and measured retrieval baseline.
- OpenTelemetry, Prometheus, Grafana, secret scanning, architecture checks,
  CI, production images, and synthetic seed tooling.
- Responsive Next.js workspace, authentication, onboarding, knowledge, cited
  chat, artifact, integration, membership, settings, and system-state screens.
- Synthetic read-only behavior, typed API/SSE adapters, mobile navigation, and
  automated WCAG accessibility regression tests.

## Live Supabase acceptance

- A real Supabase Free project is active in Mumbai.
- All versioned schema migrations, forced RLS policies, pgvector, and the
  private `clientatlas-sources` Storage bucket are applied.
- The browser-safe project URL and publishable key are configured only in an
  ignored local environment file.
- The dedicated database runtime role is separate from migration ownership,
  `NOBYPASSRLS`, and restricted to the fixed `authenticated` role.

## External acceptance still required

- The real Supabase project must complete the authenticated Storage signed-URL
  matrix with two tenants.
- A Google development OAuth app must exercise real Picker and revocation.
- Ollama models must be downloaded for generation, citation, and abstention
  evaluation.
- A configured authenticated frontend session must complete the live Supabase
  and FastAPI acceptance flow; the unconfigured default remains synthetic.
- A free public host must be deployed with synthetic read-only data.
- The demonstration video must be recorded after the frontend and URL exist.

These external gates are not silently reported as completed tests.
