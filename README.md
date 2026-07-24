# ClientAtlas

ClientAtlas is an evidence-backed client onboarding workspace for agencies,
consultancies, implementation teams, and customer-success teams. It turns
client documents into cited answers, editable onboarding briefs, readiness
reports, and action plans.

This repository is currently in the architecture and product-definition phase.
The V1 design is frozen around a zero-cash-cost constraint.

## V1 architecture

```text
Next.js web application and Node.js route handlers
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

## Implemented backend slice

- Headless Next.js route handlers for health, organizations, and workspaces
- Strict Supabase asymmetric-JWT verification
- Shared claims plus effective-role database contract in TypeScript and Python
- Drizzle schema for organizations, memberships, workspaces, and audit events
- Checksum-protected SQL migrations with forced RLS
- Deterministic cross-tenant and pooled-connection regression tests
- FastAPI service foundation with strict settings, JWT verification, and health
- Local pgvector Docker service

No application frontend has been created.

## Local backend setup

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

Copy `.env.example` values into the process environment before starting the
headless product API. A real Supabase project or local Supabase Auth instance is
required to issue tokens and expose JWKS; the standalone PostgreSQL container
only provides the database and RLS test environment.

```bash
npm run dev:api
npm run dev:ai
```

Implemented routes:

| Service | Method and path | Purpose |
| --- | --- | --- |
| Product API | `GET /api/health` | Unauthenticated liveness |
| Product API | `GET /api/v1/organizations` | List caller organizations |
| Product API | `POST /api/v1/organizations` | Create organization plus owner |
| Product API | `GET /api/v1/organizations/:id/workspaces` | List workspaces |
| Product API | `POST /api/v1/organizations/:id/workspaces` | Create workspace |
| AI service | `GET /health` | Unauthenticated liveness |

Run verification:

```bash
npm run check
npm run build
npm run check:python
```

The database integration suites additionally require `TEST_*` or
`CLIENTATLAS_TEST_*` URLs as shown in `.github/workflows/ci.yml`.
