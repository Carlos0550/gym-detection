"""Punto de entrada FastAPI.

Etapa 0:
    - App inicializada con configuración.
    - Healthcheck en GET /health.
    - CORS configurado para el frontend.
    - Lifespan placeholder (en Etapa 3 se precarga InsightFace).

Etapas siguientes agregan routers de auth, gyms, members, etc. en
``app.api.v1``.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_v1_router
from app.core.config import get_settings

settings = get_settings()

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Lifespan de la app. Etapa 3 carga aquí el motor InsightFace."""
    logger.info(
        "app.startup",
        environment=settings.environment,
        face_model=settings.face_model_name,
        face_provider=settings.face_execution_provider,
    )
    yield
    logger.info("app.shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Gym Detection API",
        version="0.1.0",
        description="Sistema de reconocimiento facial para gimnasios.",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_v1_router)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()
