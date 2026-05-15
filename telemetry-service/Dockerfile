FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

FROM python:3.12-slim-bookworm
WORKDIR /app

# --- NOVO: Instalação do curl para o healthcheck ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
COPY ./telemetry-service .
ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "server.py"]