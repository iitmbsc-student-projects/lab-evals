# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:0.9.21 AS uv

FROM python:3.13-slim

# Copy uv from the official image
COPY --from=uv /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock* ./

# Install dependencies globally using uv
RUN uv pip install --system -r pyproject.toml

# Copy application code
COPY . .

# Expose the application port (Cloud Run injects $PORT; default 8000 for local)
EXPOSE 8000

# Run the uvicorn server. Shell form so ${PORT:-8000} expands at runtime.
CMD exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
