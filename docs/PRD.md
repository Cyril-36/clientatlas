# ClientAtlas V1 Product Requirements

| Field | Value |
| --- | --- |
| Status | Frozen |
| Date | 2026-07-24 |
| Product | ClientAtlas (working title) |
| Delivery model | Local confidential mode plus synthetic read-only public demo |
| Budget | Zero cash cost |

## 1. Product summary

ClientAtlas helps client-facing delivery teams convert fragmented onboarding
material into an evidence-backed workspace. Users can ingest documents, ask
questions with citations, identify missing information, and produce editable
onboarding deliverables that retain links to their supporting sources.

The product is not a general-purpose "chat with documents" application. Its
primary outcome is reducing the time between receiving client material and
producing a reviewable onboarding plan.

## 2. Target users

### Primary users

- Implementation and onboarding managers
- Customer-success managers
- Consultants and agency delivery leads
- Solutions architects inheriting a new client account

### User jobs

1. Understand an unfamiliar client without repeatedly searching many files.
2. Distinguish source-backed facts from assumptions and missing information.
3. Prepare a brief that another team member can review and edit.
4. Identify risks, dependencies, owners, and unanswered questions early.
5. Demonstrate why an answer or recommendation was produced.

## 3. Product principles

1. **Evidence before fluency.** A concise abstention is better than an
   unsupported answer.
2. **Tenant isolation is a database invariant.** Application filters are not the
   security boundary.
3. **Documents are untrusted input.** Retrieved text cannot change system
   instructions or authorize actions.
4. **Generated outputs remain editable.** Users own the final onboarding
   deliverable.
5. **Quality is measurable.** Retrieval, citation, abstention, security, and
   latency are covered by versioned evaluations.
6. **Free deployment limits are visible.** The public demo must not imply an
   enterprise SLA.

## 4. Delivery modes

### 4.1 Local confidential mode

The complete product runs locally. It supports authentication, uploads, Google
Drive development-mode OAuth, ingestion, retrieval, generation, editing,
re-indexing, and deletion. Lightweight downloaded Hugging Face models are the
default embedding and generation providers for confidential documents.

### 4.2 Public portfolio demo

The hosted demo:

- contains fictional organizations, documents, conversations, and evaluation
  examples;
- is read-only for anonymous visitors;
- disables anonymous uploads, connectors, and administrative actions;
- rate-limits chat and generation;
- may show a cold-start or inactive-project notice;
- never accepts confidential or personal client content; and
- uses only free infrastructure quotas.

## 5. V1 functional requirements

### Identity and tenancy

- **FR-001:** Users can authenticate through Supabase Auth.
- **FR-002:** An authenticated user can create an organization.
- **FR-003:** Organization owners can create client workspaces.
- **FR-004:** Organizations support owner, admin, editor, and viewer
  memberships.
- **FR-005:** Every tenant-owned database row has an `organization_id`; every
  workspace-owned row also has a `workspace_id`.
- **FR-006:** PostgreSQL RLS enforces organization membership for every
  user-scoped read and write.

### Sources and ingestion

- **FR-010:** Editors can upload PDF and DOCX files in local confidential mode.
- **FR-011:** Files are validated by declared type, detected type, size, and
  supported extension before parsing.
- **FR-012:** A document displays an ingestion state: queued, parsing, chunking,
  embedding, ready, failed, or deleting.
- **FR-013:** A failed ingestion records a safe error code and can be retried.
- **FR-014:** Editors can re-index a source without creating duplicate active
  chunks.
- **FR-015:** Editors can delete a source and its active application records,
  extracted content, chunks, vectors, cached results, and unedited generated
  drafts whose complete evidence set came from that source. User-edited or
  multi-source artifacts are retained, stripped of affected evidence links, and
  marked for review.
- **FR-016:** Google Drive Picker can grant access to explicitly selected files
  using narrow OAuth permissions.
- **FR-017:** Source metadata includes checksum, version, last indexed time, and
  source locator.

### Retrieval and answers

- **FR-020:** Retrieval applies organization and workspace authorization before
  ranking.
- **FR-021:** Retrieval combines PostgreSQL full-text and pgvector candidates.
- **FR-022:** Reciprocal rank fusion produces the final candidate ordering.
- **FR-023:** Answers stream to the client.
- **FR-024:** Every factual answer claim is linked to one or more retrieved
  source locations.
- **FR-025:** Citations open the relevant document location or an extracted-text
  preview when the original format cannot be deep-linked.
- **FR-026:** The system abstains when the retrieved evidence is insufficient or
  contradictory.
- **FR-027:** Conversation history is isolated by organization, workspace, and
  user authorization.

### Onboarding deliverables

- **FR-030:** Users can generate an onboarding brief from workspace evidence.
- **FR-031:** Brief sections are represented as validated structured output
  before rendering.
- **FR-032:** Users can edit and save new brief versions.
- **FR-033:** Evidence links remain attached to generated claims after editing
  unless the user explicitly removes them.
- **FR-034:** The Onboarding Readiness Report identifies supported facts,
  missing information, contradictions, stale sources, risks, and suggested
  follow-up questions.
- **FR-035:** Users can produce a versioned 30/60/90-day action plan as an
  artifact.

### Quality and operations

- **FR-040:** A versioned evaluation dataset contains 30-50 reviewed questions,
  including answerable, unanswerable, contradictory, and adversarial examples.
- **FR-041:** Evaluation runs capture configuration, dataset version, per-case
  results, aggregate metrics, and failures.
- **FR-042:** Security tests deterministically exercise cross-tenant database
  retrieval and Storage access.
- **FR-043:** Prompt-injection tests verify that document instructions cannot
  alter system policy or trigger unauthorized actions.
- **FR-044:** OpenTelemetry spans cover ingestion, retrieval, generation, and
  artifact creation.
- **FR-045:** Local Prometheus and Grafana dashboards show request latency,
  ingestion failures, retrieval volume, model usage, and evaluation results.

## 6. Non-functional requirements

### Security

- **NFR-001:** Next.js and FastAPI validate token signature, issuer, audience,
  expiry, and subject before using claims.
- **NFR-002:** User-scoped direct PostgreSQL queries use the shared
  verified-claims transaction contract defined in the architecture RFC.
- **NFR-003:** User-scoped connections use a non-owner `NOBYPASSRLS` login role
  that can assume the fixed application role covered by policies.
- **NFR-004:** Tenant tables enable and force RLS.
- **NFR-005:** Migration, worker, and user-runtime credentials are separate.
- **NFR-006:** Service-role clients never share cookie handling, modules, or
  lifecycle with user-scoped clients.
- **NFR-007:** Signed object URLs are short-lived and issued only after a fresh
  authorization check.
- **NFR-008:** Logs and traces exclude document bodies, OAuth tokens, JWTs,
  provider keys, and signed URLs.
- **NFR-009:** All request inputs and model outputs are schema-validated.
- **NFR-010:** SQL identifiers and role names are fixed in code; request input is
  only passed as parameterized values.

### Reliability and performance

- **NFR-020:** Ingestion operations are idempotent by source version and
  checksum.
- **NFR-021:** Retriable failures use bounded attempts and visible terminal
  states.
- **NFR-022:** Public-demo cold starts are handled as a known degraded state, not
  reported as application failure.
- **NFR-023:** Chat cancellation stops downstream generation where supported.
- **NFR-024:** Provider timeouts return a recoverable error without losing the
  conversation or artifact draft.

### Portability and cost

- **NFR-030:** V1 incurs no mandatory cash expenditure.
- **NFR-031:** Model, embedding, storage, and queue interfaces are replaceable
  without changing product-domain code.
- **NFR-032:** The local application does not require a paid cloud account.
- **NFR-033:** Free-tier exhaustion pauses or rejects work rather than causing
  charges.

## 7. Quality gates

The first evaluated baseline establishes realistic thresholds. V1 cannot be
declared complete unless it meets all security gates and the following proposed
quality targets on the frozen evaluation dataset:

| Gate | Target |
| --- | --- |
| Cross-tenant database retrieval | 0 unauthorized rows in deterministic tests |
| Cross-tenant Storage access | 0 unauthorized objects or usable signed URLs |
| Retrieval Recall@10 | At least 0.85 |
| Citation precision | At least 0.95 |
| Unanswerable-question abstention accuracy | At least 0.90 |
| Structured artifact schema validity | 100% |
| Unsupported critical claims in approved demo artifacts | 0 |

Changing a prompt, model, embedding model, chunking policy, fusion constant, or
retrieval filter requires a new evaluation run against the same dataset version.

## 8. Explicitly deferred

- Notion and additional connectors
- PPTX and CSV parsing
- Redis and distributed queues
- NestJS as a separate product API
- Azure deployment and multiple cloud environments
- Reranking models
- Knowledge graphs
- Agentic tool loops and autonomous actions
- Real-time multi-user editing
- Enterprise SSO, SCIM, billing, and paid plans
- Immediate erasure guarantees for infrastructure-provider backups

## 9. V1 completion definition

V1 is complete only when:

1. every functional requirement marked for V1 has an automated test or a
   recorded acceptance check;
2. all quality gates pass on a fresh environment;
3. the public synthetic demo is accessible without a paid dependency;
4. the local confidential flow is demonstrated end to end;
5. the RFC, threat model, schema, runbook, and evaluation results match the
   implemented system;
6. the demonstration video shows both product behavior and evidence of quality;
   and
7. measured results, rather than planned capabilities, are available for CV
   bullet points.
