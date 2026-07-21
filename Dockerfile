FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.30 \
    /uv \
    /uvx \
    /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_CACHE=1 \
    UV_NO_DEV=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./

RUN uv sync \
    --locked \
    --no-install-project

COPY alembic.ini ./
COPY src ./src

RUN useradd \
    --system \
    --uid 10001 \
    appuser

USER appuser

EXPOSE 8000

CMD ["uvicorn", "linkup.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
