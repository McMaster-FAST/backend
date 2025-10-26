# 1st Stage: Build dependencies.
FROM ghcr.io/astral-sh/uv:0.9.5-python3.13-trixie-slim AS builder

ARG APP_ROOT=/app

WORKDIR ${APP_ROOT}
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen


# 2nd Stage: Copy dependencies and application code.
FROM ghcr.io/astral-sh/uv:0.9.5-python3.13-trixie-slim AS runner

ARG APP_ROOT=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR ${APP_ROOT}

# Copy virtual environment from builder
COPY --from=builder ${APP_ROOT}/.venv ${APP_ROOT}/.venv

# Copy Application files
COPY . .

EXPOSE 8000

CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
