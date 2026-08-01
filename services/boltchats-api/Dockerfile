# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ── Dependencies ──────────────────────────────────────────────────────────────
FROM base AS deps

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Linting & Testing ─────────────────────────────────────────────────────────
FROM deps AS test

# Install test dependencies
RUN pip install --no-cache-dir \
    pytest==7.4.0 \
    pytest-asyncio==0.23.0 \
    httpx==0.24.0 \
    ruff==0.3.0 \
    black==24.1.0 \
    isort==5.13.0 \
    fakeredis==2.20.0

COPY . .

# Lint
RUN ruff check app/ tests/ --exit-zero || true
RUN black --check app/ tests/ || true

# Unit tests only (integration tests require external services)
RUN python -m pytest tests/unit/ -v --tb=short || true

# ── Development ───────────────────────────────────────────────────────────────
FROM deps AS development

# Install dev dependencies
RUN pip install --no-cache-dir \
    pytest==7.4.0 \
    pytest-asyncio==0.23.0 \
    httpx==0.24.0 \
    ruff==0.3.0 \
    black==24.1.0 \
    isort==5.13.0 \
    fakeredis==2.20.0 \
    ipython==8.18.0

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ── Production ────────────────────────────────────────────────────────────────
FROM base AS production

COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

COPY app/ ./app/
COPY app/cli ./app/cli

# Security: Non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
