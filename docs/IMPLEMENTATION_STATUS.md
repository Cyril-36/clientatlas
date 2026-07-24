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

## External acceptance still required

- A real Supabase project must run the Storage signed-URL matrix.
- A Google development OAuth app must exercise real Picker and revocation.
- Ollama models must be downloaded for generation, citation, and abstention
  evaluation.
- The separately built frontend must consume the OpenAPI and SSE contracts.
- A free public host must be deployed with synthetic read-only data.
- The demonstration video must be recorded after the frontend and URL exist.

These external gates are not silently reported as completed tests.
