# Local Development Runbook

Prerequisites are Node.js 24, npm, Python 3.11–3.13, uv, and Docker Desktop.

```bash
docker compose -f infra/local/docker-compose.yml up -d postgres
MIGRATION_DATABASE_URL=postgresql://postgres:local-migration-only@127.0.0.1:55432/clientatlas npm run db:migrate
npm ci
uv sync --project services/ai --extra dev --extra local-models --locked
npm run check
npm run check:python
npm run build
```

Copy the example environment variables and start the services:

```bash
npm run dev:api
npm run dev:ai
```

The first authenticated request downloads `all-MiniLM-L6-v2` and
`flan-t5-small` into the normal Hugging Face cache. The public synthetic mode
does not import or download the optional local-model dependencies.

Verify the downloaded models using fictional input:

```bash
uv run --project services/ai --extra local-models python scripts/verify_local_models.py
```

After migration `0014_huggingface_minilm_embeddings.sql`, re-index every
retained source. The migration deliberately invalidates old 768-dimensional
derived chunks because embeddings from different model spaces cannot be
converted truthfully.

Leave `CLIENTATLAS_GEMINI_API_KEY` unset for confidential operation.

Start local observability with:

```bash
docker compose -f infra/local/docker-compose.yml --profile observability up -d
```

Prometheus is on port 9090, Grafana on 3001, and AI metrics on
`http://127.0.0.1:8000/metrics`.

Run `scripts/seed_demo.py`, copy its organization/workspace IDs, then run
`scripts/run_evaluation.py`. Both use only the fictional evaluation corpus.
