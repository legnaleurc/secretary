FROM python:3.12-slim-trixie AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_SYSTEM_PYTHON=1

WORKDIR /app
COPY pyproject.toml uv.lock /app/
RUN uv sync --no-dev

FROM python:3.12-slim-trixie AS production

COPY . /app
COPY --from=builder /app/.venv /app/.venv
WORKDIR /app
