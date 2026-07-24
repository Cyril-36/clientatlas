# Agent Instructions

## Scope
- Build backend, database, AI, tests, infrastructure, and documentation.
- Do not create pages, components, styles, design tokens, or other frontend UI.
- Keep `apps/product-api` limited to Next.js route handlers and server modules.
- Treat `docs/architecture/RFC-001-clientatlas-v1.md` as the frozen contract.

## Package Managers
- Node.js: npm workspaces; use `npm install`, `npm run check`, `npm test`.
- Python: uv; use `uv sync --project services/ai --extra dev`.

## Security Invariants
- User database calls require verified JWT claims and `SET LOCAL ROLE authenticated`
  in the same transaction.
- Runtime roles are non-owner and `NOBYPASSRLS`.
- Never import migration or worker credentials into user-request modules.
- Never send non-synthetic content to Gemini.
- Add deterministic cross-tenant tests for every tenant-owned query.

## File-Scoped Commands
| Task | Command |
| --- | --- |
| TypeScript lint | `npx eslint path/to/file.ts` |
| TypeScript test | `npx vitest run path/to/file.test.ts` |
| Python lint | `uv run --project services/ai ruff check path/to/file.py` |
| Python test | `uv run --project services/ai pytest path/to/test.py` |

## Database
- Drizzle schema: `packages/database/src/schema.ts`.
- SQL migrations: `packages/database/migrations/`.
- SQL identifiers and role names must be fixed constants, never request input.
- Enable and force RLS on every tenant-owned table.

## Commit Attribution
AI commits MUST include:
```text
Co-Authored-By: (the agent model's name and attribution byline)
```

