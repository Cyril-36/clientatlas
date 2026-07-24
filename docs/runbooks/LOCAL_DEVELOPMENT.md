# Local Development Runbook

Prerequisites are Node.js 24, npm, Python 3.11–3.13, uv, Docker Desktop, and
Ollama for real local embeddings and generation.

```bash
docker compose -f infra/local/docker-compose.yml up -d postgres
MIGRATION_DATABASE_URL=postgresql://postgres:local-migration-only@127.0.0.1:55432/clientatlas npm run db:migrate
npm ci
uv sync --project services/ai --extra dev --locked
npm run check
npm run check:python
npm run build
```

Copy the example environment variables and start the services:

```bash
npm run dev:api
npm run dev:ai
```

For local models:

```bash
ollama pull nomic-embed-text
ollama pull qwen2.5:7b
```

Leave `CLIENTATLAS_GEMINI_API_KEY` unset for confidential operation.

Start local observability with:

```bash
docker compose -f infra/local/docker-compose.yml --profile observability up -d
```

Prometheus is on port 9090, Grafana on 3001, and AI metrics on
`http://127.0.0.1:8000/metrics`.

Run `scripts/seed_demo.py`, copy its organization/workspace IDs, then run
`scripts/run_evaluation.py`. Both use only the fictional evaluation corpus.
