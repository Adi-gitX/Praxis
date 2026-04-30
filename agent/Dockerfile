# syntax=docker/dockerfile:1.7
# Multi-stage build for the Praxis Python agent: poetry install -> slim runtime.

FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=2.3.4 \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

# --- builder ----------------------------------------------------------------
FROM base AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential curl git \
    && rm -rf /var/lib/apt/lists/*
RUN pip install "poetry==${POETRY_VERSION}"

WORKDIR /app/agent
COPY pyproject.toml poetry.lock README.md ./
RUN poetry install --only main --no-root

COPY src ./src
COPY configs ./configs
RUN poetry install --only main

# --- runtime ----------------------------------------------------------------
FROM base AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash praxis

WORKDIR /app/agent
COPY --from=builder --chown=praxis:praxis /app/agent /app/agent
USER praxis

ENV PATH="/app/agent/.venv/bin:${PATH}" \
    PYTHONPATH="/app/agent/src" \
    PRAXIS_RUNS_DIR="/app/runs"

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health',timeout=3).status==200 else 1)" || exit 1

CMD ["uvicorn", "praxis.server:app", "--host", "0.0.0.0", "--port", "8000"]
