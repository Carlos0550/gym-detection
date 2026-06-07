# syntax=docker/dockerfile:1.7

# ============================================================
# Backend: FastAPI + SQLAlchemy async + Alembic + InsightFace
# ============================================================
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

# --- System deps ---
# build-essential: compilar deps puntuales
# libgl1, libglib2.0-0, libsm6, libxext6, libxrender1: runtime de OpenCV
# (InsightFace importa cv2 y los necesita en runtime)
# curl: healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# --- uv (gestor de deps) ---
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# --- Crear usuario no root ---
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# --- Venv con python del sistema (NO uv venv: crea symlinks a paths del host) ---
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app

RUN python -m venv /app/.venv && \
    chown -R appuser:appuser /app/.venv

# --- Deps (cache de layer) ---
# Copiamos pyproject.toml y la app entera (en build time)
COPY pyproject.toml ./
# En este Dockerfile (dev) instalamos el proyecto + el grupo dev con
# pytest/ruff. En producción se debería usar otro Dockerfile multi-stage
# que sólo instale las deps de runtime.
RUN uv pip install --python /app/.venv/bin/python --group dev -e .

# --- Código (en runtime se sobreescribe con el volumen) ---
COPY --chown=appuser:appuser . .

# --- Permisos y dirs runtime ---
RUN mkdir -p /home/appuser/.insightface && \
    chown -R appuser:appuser /home/appuser/.insightface

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl --fail --silent http://localhost:8000/health || exit 1

# Usamos uvicorn directo (no "uv run") para que no intente re-sync al ver pyproject
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
