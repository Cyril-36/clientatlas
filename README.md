# ClientAtlas

**Evidence-backed client onboarding, from scattered documents to a reviewable
plan.**

ClientAtlas is a production-oriented AI knowledge workspace for implementation
teams, consultants, agencies, and customer-success teams. It ingests client
material, answers questions with source citations, identifies missing
information, and produces editable onboarding briefs, readiness reports, and
action plans.

This repository is intentionally more than a “chat with PDFs” demo. It focuses
on the engineering problems that determine whether a multi-tenant RAG product
is trustworthy: database-enforced tenant isolation, evidence traceability,
abstention, untrusted-document handling, reproducible evaluation, and explicit
privacy boundaries.

> **Current state:** the V1 application, AI service, database, evaluation suite,
> observability stack, and responsive interface are implemented. A real
> Supabase Free project is configured. Public hosting, the final authenticated
> Storage acceptance flow, Google OAuth acceptance, and the demonstration video
> remain release gates.

## What ClientAtlas does

| Capability | V1 behavior |
| --- | --- |
| Knowledge ingestion | Validates and indexes PDF and DOCX files with visible ingestion states, bounded retries, re-indexing, and active-data deletion |
| Hybrid retrieval | Combines PostgreSQL full-text search and pgvector candidates with reciprocal rank fusion |
| Cited answers | Streams plain-text answers with allowlisted evidence citations and abstains when support is insufficient |
| Onboarding deliverables | Creates editable, versioned onboarding briefs, readiness reports, and 30/60/90-day action plans |
| Google Drive | Uses Picker, PKCE, `drive.file`, one-use OAuth state, encrypted refresh tokens, and revocation |
| Tenant security | Enforces organization membership with PostgreSQL RLS instead of relying on application filters |
| Quality evaluation | Runs a versioned 30-question synthetic suite covering answerable, unanswerable, contradictory, and prompt-injection cases |
| Operations | Emits OpenTelemetry traces and Prometheus metrics with a local Grafana stack |

The interface includes workspace overview, knowledge library, cited chat,
artifact editing, readiness reporting, action planning, integrations, member
administration, settings, onboarding, authentication, loading, empty, and safe
error states.

## Architecture

```mermaid
flowchart LR
    U["Browser"] --> N["Next.js product application"]
    N --> A["Supabase Auth"]
    N --> T["Node.js route handlers"]
    T --> D["Drizzle verified-claims transaction"]
    N --> F["FastAPI AI service"]
    F --> P["Python verified-claims transaction"]
    D --> DB["Supabase PostgreSQL + pgvector"]
    P --> DB
    N --> S["Private Supabase Storage"]
    F --> H["Lightweight Hugging Face models"]
    F --> G["Gemini synthetic-only adapter"]
    T --> OT["OpenTelemetry"]
    F --> OT
    OT --> M["Prometheus + Grafana"]
```

### Stack

- **Product application:** Next.js, React, TypeScript, Node.js route handlers
- **Data layer:** Drizzle ORM, PostgreSQL 17, pgvector, forced RLS
- **AI service:** Python, FastAPI, SQLAlchemy, hybrid retrieval, SSE streaming
- **Identity and files:** Supabase Auth and private Supabase Storage
- **Local models:** Sentence Transformers with `all-MiniLM-L6-v2` and
  Transformers with `flan-t5-small`
- **Quality and operations:** Vitest, Pytest, jest-axe, OpenTelemetry,
  Prometheus, Grafana, GitHub Actions

## Security model

A direct Drizzle or SQLAlchemy connection does not automatically propagate a
Supabase user into PostgreSQL. ClientAtlas therefore treats verified JWT claims
and the effective PostgreSQL role as separate controls.

Every user-scoped query follows this transaction contract:

```text
verify JWT signature, issuer, audience, expiry, subject, and role
        ↓
open transaction using clientatlas_runtime
        ↓
SET LOCAL request.jwt.claims
        ↓
SET LOCAL ROLE authenticated
        ↓
execute the tenant query under forced RLS
        ↓
commit or roll back; claims and role disappear
```

Security invariants include:

- the runtime login is non-owner, non-superuser, and `NOBYPASSRLS`;
- every tenant-owned table enables and forces RLS;
- TypeScript and Python use the same verified-claims transaction boundary;
- migration, worker, runtime, and browser credentials remain separate;
- SQL identifiers and role names are fixed constants;
- Storage policies are tested independently from database RLS;
- security-definer functions use an empty fixed `search_path` and narrow grants;
- retrieved documents are untrusted data, never instructions or authority;
- service-role credentials never enter browser or user-request modules; and
- confidential material is never sent to the unpaid Gemini API.

See the [architecture RFC](docs/architecture/RFC-001-clientatlas-v1.md) and
[threat model](docs/security/THREAT_MODEL.md) for the complete contract.

## Measured quality

The committed deterministic retrieval baseline uses 24 cases with expected
sources from the versioned synthetic dataset.

| Metric | Result |
| --- | ---: |
| Recall@10 | **1.000** |
| Mean reciprocal rank | **0.847** |
| Mean nDCG | **0.884** |
| Cross-tenant database leakage | **0 unauthorized rows** |
| Application tables with forced RLS | **14 / 14** |
| Automated frontend/API tests | **46 passing** |
| Deterministic database RLS tests | **6 passing** |
| Supabase security-advisor findings | **0** |

The deterministic hash embedding is a reproducible test baseline, not a
production model-quality claim. Citation precision and abstention evaluation
are implemented, but generation scores remain unclaimed until the lightweight
Hugging Face run is repeated and reviewed. Details are in
[docs/EVALUATION.md](docs/EVALUATION.md).

## Zero-cost delivery model

V1 is designed to require no mandatory cash expenditure:

- **Local confidential mode** runs the complete ingestion, retrieval, editing,
  and generation flow with downloaded Hugging Face models.
- **Public portfolio mode** is synthetic and read-only. Uploads, OAuth,
  generation mutations, administration, and deletion are disabled.
- **Supabase Free** provides Auth, PostgreSQL, pgvector, and private object
  storage within its free quotas.

Free-tier limitations are part of the product contract. ClientAtlas does not
claim an enterprise SLA, immediate provider-backup erasure, unlimited model
usage, or dependable always-on background workers.

## Repository layout

```text
apps/product-api/          Next.js UI, route handlers, Supabase browser adapter
packages/database/         Drizzle schema, SQL migrations, RLS integration tests
packages/evaluation/       Synthetic corpus, question dataset, measured reports
packages/contracts/        Generated AI-service OpenAPI contract
services/ai/               FastAPI ingestion, retrieval, chat, and artifacts
infra/local/               PostgreSQL, OpenTelemetry, Prometheus, and Grafana
scripts/                   Architecture checks, demo seeding, and evaluation
docs/                      PRD, RFC, threat model, API, runbooks, and backlog
```

## Run locally

### Prerequisites

- Node.js 24+
- npm
- Python 3.11–3.13
- [uv](https://docs.astral.sh/uv/)
- Docker Desktop
- Enough local disk and memory for the optional lightweight Hugging Face models

### 1. Install dependencies

```bash
npm ci
uv sync --project services/ai --extra dev --extra local-models --locked
```

### 2. Start PostgreSQL and apply migrations

```bash
docker compose -f infra/local/docker-compose.yml up -d postgres

MIGRATION_DATABASE_URL=postgresql://postgres:local-migration-only@127.0.0.1:55432/clientatlas \
  npm run db:migrate
```

### 3. Configure the environment

Use [.env.example](.env.example) and
[services/ai/.env.example](services/ai/.env.example) as the templates.

The browser may receive only:

```text
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
NEXT_PUBLIC_AI_API_URL
NEXT_PUBLIC_DEMO_MODE
```

Never expose database passwords, migration credentials, OAuth client secrets,
encryption keys, or a Supabase service-role key through a `NEXT_PUBLIC_`
variable.

With no browser-safe Supabase configuration, the UI defaults to the fictional,
read-only demo. Set `NEXT_PUBLIC_DEMO_MODE=false` only for an authenticated
local flow.

### 4. Start the services

```bash
npm run dev:api
npm run dev:ai
```

- Product application: `http://127.0.0.1:3000/overview`
- Product health: `http://127.0.0.1:3000/api/health`
- AI health: `http://127.0.0.1:8000/health`
- AI OpenAPI: `http://127.0.0.1:8000/docs`

The first authenticated local model request downloads
`sentence-transformers/all-MiniLM-L6-v2` and `google/flan-t5-small` into the
normal Hugging Face cache. No Ollama daemon is required. The synthetic public
demo does not load either model.

Verify both local models with fictional input:

```bash
uv run --project services/ai --extra local-models \
  python scripts/verify_local_models.py
```

Leave `CLIENTATLAS_GEMINI_API_KEY` unset for confidential operation.

## Verification

Run the complete static, unit, accessibility, and Python checks:

```bash
npm run check
npm run build
npm run check:python
```

Database integration suites require the test URLs shown in
[.github/workflows/ci.yml](.github/workflows/ci.yml). The CI workflow also
checks architecture boundaries, secret patterns, migration integrity, and the
production build.

Start the optional observability stack with:

```bash
docker compose -f infra/local/docker-compose.yml \
  --profile observability up -d
```

Prometheus runs on port `9090` and Grafana on port `3001`.

## Documentation

- [Product requirements](docs/PRD.md)
- [Architecture RFC](docs/architecture/RFC-001-clientatlas-v1.md)
- [Lightweight local-model amendment](docs/architecture/RFC-002-lightweight-local-models.md)
- [Data model and RLS contract](docs/DATA_MODEL.md)
- [API and SSE contract](docs/API.md)
- [Frontend routes and accessibility](docs/FRONTEND.md)
- [Threat model](docs/security/THREAT_MODEL.md)
- [Dependency risk register](docs/security/DEPENDENCY_RISK.md)
- [Evaluation method and results](docs/EVALUATION.md)
- [Supabase Free runbook](docs/runbooks/SUPABASE_FREE.md)
- [Local development runbook](docs/runbooks/LOCAL_DEVELOPMENT.md)
- [Implementation status](docs/IMPLEMENTATION_STATUS.md)

## Release status

The remaining external acceptance gates are tracked explicitly:

- complete the authenticated two-tenant Storage signed-URL matrix;
- exercise Google Picker and token revocation with a development OAuth app;
- repeat retrieval, generation, citation, and abstention evaluation with the
  lightweight local Hugging Face models;
- complete the authenticated frontend-to-FastAPI acceptance flow;
- deploy the synthetic read-only public demo; and
- record the demonstration video.

Until those gates pass, the repository describes V1 as implemented and
verified locally—not as a fully deployed production service.
