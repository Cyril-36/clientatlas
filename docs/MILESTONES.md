# ClientAtlas V1 Milestone Backlog

| Field | Value |
| --- | --- |
| Status | Frozen V1 delivery plan |
| Date | 2026-07-24 |
| Assumption | One primary developer, approximately 8-10 weeks |
| Budget | Zero mandatory cash cost |

## 1. Delivery rules

- Each milestone ends with demonstrable behavior and evidence.
- Security tests are implemented with the feature they protect, not postponed to
  the final week.
- Keep commits focused and reversible.
- Do not add deferred infrastructure to make the repository appear more complex.
- A green build is not completion; each milestone has explicit exit criteria.
- Public-demo behavior and local-confidential behavior are tested separately.
- Architecture changes require an RFC amendment before implementation.

## 2. Priority vocabulary

- **P0:** Required for the milestone and V1.
- **P1:** Required for V1 but can follow the milestone's first vertical slice.
- **P2:** Optional polish; cannot delay V1.
- **Deferred:** Outside V1.

## M0: Repository and executable baseline

**Goal:** Establish a reproducible, testable monorepo and protect the frozen
architecture.

### Work

- **P0** Create the monorepo structure.
- **P0** Scaffold Next.js with strict TypeScript.
- **P0** Scaffold FastAPI with typed settings and async test support.
- **P0** Add Drizzle configuration and migration workflow.
- **P0** Add local Supabase or PostgreSQL/pgvector development services.
- **P0** Add formatting, linting, type checking, unit-test, and migration-check
  commands.
- **P0** Add GitHub Actions with least-privilege workflow permissions.
- **P0** Add secret scanning and dependency review suitable for a public repo.
- **P0** Add `.env.example` files containing names only, never live values.
- **P1** Add an architecture invariant check for forbidden runtime imports.

### Proposed structure

```text
apps/
  web/                 Next.js UI, route handlers, Drizzle runtime
services/
  ai/                  FastAPI retrieval, ingestion, generation, evaluation
packages/
  contracts/           JSON schemas and generated TypeScript/Python models
  database/            Drizzle schema, migrations, seeds, policy checks
  evaluation/          Versioned synthetic corpus and expected results
infra/
  local/               Docker Compose and local telemetry configuration
docs/
  architecture/
  security/
  runbooks/
```

### Exit criteria

- A fresh clone starts the web app, API, database, and tests using documented
  commands.
- CI runs without paid services or live cloud secrets.
- The initial migration enables pgvector and establishes schemas/roles.
- No committed secret is detected.

## M1: Authentication, organizations, workspaces, and RLS

**Goal:** Prove the tenant boundary before storing client content.

### Work

- **P0** Integrate Supabase Auth with Next.js.
- **P0** Define `VerifiedClaims` and strict token verification.
- **P0** Create Drizzle tables for organizations, memberships, and workspaces.
- **P0** Create migration, user-runtime, and worker credential boundaries.
- **P0** Implement the TypeScript verified-claims transaction helper.
- **P0** Implement the Python equivalent helper.
- **P0** Apply `ENABLE ROW LEVEL SECURITY` and `FORCE ROW LEVEL SECURITY`.
- **P0** Create membership and role policies.
- **P0** Verify fixed `authenticated` role switching.
- **P0** Add transaction-pool claim/role leakage regression tests.
- **P0** Add deterministic owner/admin/editor/viewer authorization tests.
- **P0** Add cross-tenant CRUD tests in both services.
- **P1** Add audit events for organization, membership, and workspace changes.

### Exit criteria

- Forged, expired, wrong-issuer, and wrong-audience JWTs fail.
- Next.js and FastAPI return identical authorization outcomes.
- Reusing one pooled connection across two tenants leaks no role, claim, or row.
- Runtime role inspection confirms non-owner and `NOBYPASSRLS`.
- No tenant table is missing forced RLS.

## M2: PDF/DOCX upload and ingestion lifecycle

**Goal:** Convert supported local files into versioned, searchable chunks.

### Work

- **P0** Create source, document-version, chunk, and ingestion-job migrations.
- **P0** Create a private Storage bucket and policies.
- **P0** Implement server-generated object paths.
- **P0** Validate file extension, detected MIME, size, and supported format.
- **P0** Parse PDF and DOCX with bounded resources and safe failure codes.
- **P0** Implement deterministic chunking and source locators.
- **P0** Generate local embeddings through a provider interface.
- **P0** Implement checksum/version idempotency.
- **P0** Claim jobs using `FOR UPDATE SKIP LOCKED`.
- **P0** Implement bounded retries and visible states.
- **P0** Implement atomic active-version switching.
- **P0** Implement re-indexing.
- **P0** Implement active-system deletion.
- **P0** Add cross-tenant Storage and signed-URL tests.
- **P1** Add corrupt, mislabeled, oversized, encrypted, and decompression-limit
  fixtures.

### Exit criteria

- A PDF and DOCX reach `ready` with traceable chunks.
- Reprocessing the same checksum creates no duplicate active version.
- A failed parser produces a safe visible state and bounded retry.
- A deleting source disappears from retrieval immediately.
- Cross-tenant Storage list/read/write/delete/signed-URL tests all fail closed.

## M3: Hybrid retrieval

**Goal:** Retrieve tenant-safe evidence using lexical and semantic signals.

### Work

- **P0** Add generated PostgreSQL full-text vectors and indexes.
- **P0** Add pgvector similarity queries.
- **P0** Enforce organization, workspace, active-version, and source-state
  filters in both paths.
- **P0** Implement reciprocal rank fusion.
- **P0** Return stable chunk IDs, locators, and component ranks.
- **P0** Add bounded evidence selection.
- **P0** Seed near-duplicate cross-tenant canary documents.
- **P0** Add lexical and vector tenant-isolation regressions.
- **P1** Add Recall@K, MRR, and nDCG evaluators.
- **P1** Record retrieval spans and candidate counts without source text.

### Exit criteria

- Hybrid retrieval beats or matches each single retrieval path on the initial
  reviewed dataset.
- Recall@10 reaches the frozen quality target or an RFC records the measured
  blocker.
- Cross-tenant canary terms and embeddings never appear.

## M4: Streamed cited answers and abstention

**Goal:** Produce trustworthy answers without granting the model authority.

### Work

- **P0** Define a versioned answer JSON/event schema.
- **P0** Implement lightweight local Hugging Face providers.
- **P0** Implement the synthetic-only Gemini provider.
- **P0** Enforce workspace privacy mode server-side.
- **P0** Stream progress, answer, citation, completion, and safe error events.
- **P0** Delimit retrieved content as untrusted evidence.
- **P0** Validate citation IDs against the retrieved allowlist.
- **P0** Validate cited chunks against the current tenant and active source
  version.
- **P0** Implement explicit abstention behavior.
- **P0** Persist final messages only after validation.
- **P0** Sanitize rendered Markdown and disable unsafe HTML.
- **P0** Add direct and indirect prompt-injection cases.
- **P1** Implement cancellation and provider timeout handling.

### Exit criteria

- Answers stream with working evidence links.
- Invalid or invented citations are rejected.
- Unanswerable cases abstain at or above the frozen target.
- Prompt-injection fixtures cannot change provider, policy, tenant, or citation
  allowlists.
- Confidential-mode requests never invoke Gemini.

## M5: Editable artifacts and Readiness Report

**Goal:** Turn evidence into reviewable onboarding deliverables.

### Work

- **P0** Define versioned schemas for onboarding briefs, readiness reports, and
  30/60/90-day action plans.
- **P0** Generate validated structured drafts.
- **P0** Attach evidence using JSON pointers and chunk IDs.
- **P0** Implement editing and immutable version history.
- **P0** Implement draft, reviewed, approved, and archived states.
- **P0** Identify missing information, contradictions, stale sources, risks, and
  follow-up questions.
- **P0** Flag artifacts affected by source deletion or replacement.
- **P1** Add a side-by-side evidence viewer.
- **P2** Add export styling that does not delay core completion.

### Exit criteria

- Every saved artifact version passes its schema.
- Evidence links resolve only within the current tenant.
- Deleting or superseding a source visibly marks affected evidence.
- The seeded workspace produces a useful brief and Readiness Report with no
  unsupported critical claim.

## M6: Google Drive Picker

**Goal:** Add one narrow, defensible OAuth connector.

### Work

- **P0** Configure Google Drive Picker with the narrowest suitable file scope.
- **P0** Implement state validation and PKCE where supported.
- **P0** Encrypt refresh credentials at the application layer.
- **P0** Restrict credential decryption to the connector worker.
- **P0** Import explicitly selected PDF and DOCX files.
- **P0** Persist external file ID, checksum/version metadata, and granted scopes.
- **P0** Revoke the connection and remove active credentials.
- **P0** Add callback forgery, state reuse, and mismatched-account tests.
- **P1** Demonstrate source change detection and manual re-sync.

### Exit criteria

- A development-mode test user selects and ingests a Drive file.
- The application requests no broad all-Drive scope.
- OAuth credentials never appear in logs, traces, browser responses, or exports.
- Revocation prevents future sync attempts.

## M7: Evaluation, security, and observability gates

**Goal:** Turn implementation claims into reproducible evidence.

### Work

- **P0** Freeze a 30-50 case synthetic evaluation dataset.
- **P0** Cover answerable, unanswerable, contradictory, injection, and
  tenant-isolation categories.
- **P0** Record dataset, prompt, chunker, embedding, model, and code versions.
- **P0** Add deterministic retrieval and citation evaluators.
- **P0** Add bounded model-based evaluation locally as secondary evidence.
- **P0** Run the full threat-model verification matrix.
- **P0** Instrument Next.js, FastAPI, ingestion, retrieval, and generation.
- **P0** Configure local OpenTelemetry Collector, Prometheus, and Grafana.
- **P0** Add telemetry-hygiene snapshot tests.
- **P0** Publish a machine-readable and human-readable evaluation report.
- **P1** Add a regression comparison against the previous accepted run.

### Exit criteria

- All security gates pass deterministically.
- Frozen retrieval, citation, abstention, and schema targets pass.
- A fresh evaluation report identifies the tested Git commit and configuration.
- Dashboards show expected signals without source bodies or credentials.

## M8: Public demo and portfolio handoff

**Goal:** Ship a truthful, reproducible portfolio artifact.

### Work

- **P0** Create a fictional organization, workspace, documents, and questions.
- **P0** Add deterministic seed and reset commands.
- **P0** Deploy the read-only frontend and sleeping AI service on free tiers.
- **P0** Disable anonymous upload, connectors, membership changes, and deletion.
- **P0** Add rate limits and hard request/token ceilings.
- **P0** Display synthetic-data, cold-start, uptime, and privacy notices.
- **P0** Write setup, architecture, security, evaluation, and troubleshooting
  documentation.
- **P0** Add an operational runbook for free-tier pause and reset behavior.
- **P0** Record a short demonstration video showing public and local modes.
- **P0** Verify a fresh clone and deployment instructions.
- **P1** Capture measured performance and quality evidence for future CV updates.

### Exit criteria

- The public demo works without a paid dependency or confidential input.
- The local video demonstrates upload, OAuth, worker states, retrieval,
  citations, artifacts, re-indexing, and deletion.
- All documentation matches the deployed commit.
- The final evaluation and security reports are linked from the repository
  README.
- CV updates use measured outcomes only.

## 3. Deferred backlog

These items require an RFC amendment and must not enter a V1 milestone:

- Notion
- PPTX or CSV
- Redis, Celery, or another distributed queue
- NestJS product API
- Azure infrastructure
- Paid model providers
- Reranking
- Multiple cloud environments
- Knowledge graphs
- Autonomous or tool-using agents
- Real-time collaborative editing
- Billing and commercial hosting

## 4. Definition of done for each work item

A work item is done when:

- code and migration changes are reviewed together;
- unit and relevant integration tests pass;
- negative authorization behavior is tested where applicable;
- telemetry contains no prohibited data;
- errors have safe user-visible codes;
- documentation and architecture references are updated;
- no unrelated generated artifact is committed; and
- a focused commit records the completed behavior.
