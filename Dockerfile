# Multi-stage Dockerfile using Astral uv for ultra-fast Python packaging
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install dependencies first (layer caching)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application source
COPY tldr_bot/ ./tldr_bot/
COPY README.md ./
RUN uv sync --frozen --no-dev

# Final runtime image
FROM python:3.13-slim-bookworm AS runtime

WORKDIR /app

# Copy virtualenv and application code from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/tldr_bot /app/tldr_bot

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "tldr_bot.main"]
