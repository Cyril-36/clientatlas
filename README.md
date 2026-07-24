# ClientAtlas

ClientAtlas is an evidence-backed client onboarding workspace for agencies,
consultancies, implementation teams, and customer-success teams. It turns
client documents into cited answers, editable onboarding briefs, readiness
reports, and action plans.

The V1 product application is implemented around a zero-cash-cost constraint.
It includes a responsive Next.js frontend, Node.js route handlers, and the
FastAPI AI service.

## V1 architecture

```text
Next.js product application and Node.js route handlers
        |
        +-- Supabase Auth
        |
        +-- Drizzle ORM
        |       |
        |       +-- verified-claims transaction helper
        |       +-- SET LOCAL ROLE authenticated
        |       +-- Supabase PostgreSQL and pgvector
        |
        +-- FastAPI AI and ingestion service
                |
                +-- same verified-claims database contract
                +-- local Ollama for confidential content
                +-- Gemini free tier for synthetic demo content only
```

The public deployment is a seeded, synthetic, read-only portfolio demo. Upload,
OAuth, ingestion workers, re-indexing, and deletion are demonstrated locally or
through a recorded authenticated flow.

## Frozen constraints

- Cash cost must remain zero for V1.
- Drizzle remains the Node.js and TypeScript data-access layer.
- User-scoped database work must execute under PostgreSQL RLS.
- Direct database services must establish both verified JWT claims and the
  effective PostgreSQL role inside one transaction.
- Service-role credentials are isolated from user-scoped clients.
- Gemini receives fictional demonstration material only.
- The project makes no claim that provider backups are immediately erased.
- Notion, Redis, Azure, reranking, complex agents, and additional connectors are
  deferred.

## Planning documents

- [Product requirements](docs/PRD.md)
- [Architecture RFC](docs/architecture/RFC-001-clientatlas-v1.md)
- [Threat model](docs/security/THREAT_MODEL.md)
- [Dependency risk register](docs/security/DEPENDENCY_RISK.md)
- [Data model and RLS contract](docs/DATA_MODEL.md)
- [Milestone backlog](docs/MILESTONES.md)
- [External references](docs/REFERENCES.md)

## Status vocabulary

- **Frozen:** accepted for V1; changes require an RFC amendment.
- **Deferred:** intentionally excluded from V1.
- **Proposed:** not yet accepted.

## Implemented V1

- Responsive ClientAtlas workspace UI based on the Kinetic Enterprise design
- Synthetic read-only demo data with administrative mutations disabled
- Optional Supabase browser authentication using the public anonymous key
- Typed product API, upload, and SSE chat client boundaries
- Next.js route handlers for health, organizations, and workspaces
- Strict Supabase asymmetric-JWT verification
- Shared claims plus effective-role database contract in TypeScript and Python
- Drizzle schema for organizations, memberships, workspaces, and audit events
- Checksum-protected SQL migrations with forced RLS
- Deterministic cross-tenant and pooled-connection regression tests
- FastAPI service foundation with strict settings, JWT verification, and health
- Local pgvector Docker service
- PDF/DOCX ingestion with bounded parsing, chunking, re-indexing, and deletion
- PostgreSQL full-text plus pgvector hybrid retrieval with RRF
- Streamed plain-text answers with validated citations and abstention
- Ollama-first generation and synthetic-only Gemini routing
- Editable evidence-linked onboarding artifacts with immutable history
- PKCE Google Drive `drive.file` connector with private encrypted credentials
- Thirty-case evaluation suite and measured retrieval report
- OpenTelemetry, Prometheus, Grafana, architecture, and secret-scanning gates

Product and integration references:

- [API and frontend contract](docs/API.md)
- [Frontend modes and routes](docs/FRONTEND.md)
- [Exact implementation status](docs/IMPLEMENTATION_STATUS.md)
- [Evaluation results and method](docs/EVALUATION.md)
- [Local runbook](docs/runbooks/LOCAL_DEVELOPMENT.md)
- Generated OpenAPI: `packages/contracts/openapi/ai-service.json`

## Local setup

Requirements: Node.js 24, npm, Python 3.11-3.13, uv, and Docker.

```bash
npm ci
uv sync --project services/ai --extra dev
docker compose -f infra/local/docker-compose.yml up -d postgres
```

Apply the local migration:

```bash
MIGRATION_DATABASE_URL=postgresql://postgres:local-migration-only@127.0.0.1:55432/clientatlas npm run db:migrate
```

For the configured free Supabase project, credential boundaries, and live
verification checklist, see
[`docs/runbooks/SUPABASE_FREE.md`](docs/runbooks/SUPABASE_FREE.md).

Copy `.env.example` values into the process environment. Without browser-safe
Supabase variables the UI starts in a synthetic read-only demonstration mode.
A real Supabase project or local Supabase Auth instance is required to issue
tokens and expose JWKS; the standalone PostgreSQL container only provides the
database and RLS test environment.

```bash
npm run dev:api
npm run dev:ai
```

The complete route, request, response, SSE, and frontend-security contracts are
documented in [API and frontend contract](docs/API.md). Liveness endpoints are
`GET /api/health` for the product API and `GET /health` for the AI service.

Run verification:

```bash
npm run check
npm run build
npm run check:python
```

The database integration suites additionally require `TEST_*` or
`CLIENTATLAS_TEST_*` URLs as shown in `.github/workflows/ci.yml`.
