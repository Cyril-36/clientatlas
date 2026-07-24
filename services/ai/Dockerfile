FROM ghcr.io/astral-sh/uv:0.8.8 AS uv

FROM python:3.12-slim AS builder
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
WORKDIR /app

COPY --from=uv /uv /uvx /bin/
COPY services/ai/pyproject.toml services/ai/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY services/ai/src src
RUN uv sync --frozen --no-dev

FROM python:3.12-slim AS runner
ENV PATH=/app/.venv/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN addgroup --system --gid 1001 clientatlas \
    && adduser --system --uid 1001 --ingroup clientatlas clientatlas

COPY --from=builder --chown=clientatlas:clientatlas /app /app

USER clientatlas
EXPOSE 8000
CMD ["uvicorn", "clientatlas_ai.main:app", "--host", "0.0.0.0", "--port", "8000"]

