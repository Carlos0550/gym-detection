"""Punto de entrada FastAPI."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.api.v1 import api_v1_router
from app.core.config import get_settings
from app.core.logging import logger
from app.modules.face.engine import FaceEngine

settings = get_settings()


def _run_migrations() -> None:
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "app.startup",
        environment=settings.environment,
        face_model=settings.face_model_name,
        face_provider=settings.face_execution_provider,
    )

    if settings.auto_migrate:
        logger.info("app.migrate.start")
        await asyncio.to_thread(_run_migrations)
        logger.info("app.migrate.done")

    face_engine = FaceEngine(settings)
    app.state.face_engine = face_engine
    if face_engine.is_loaded:
        logger.info("app.face_engine.ready")
    else:
        logger.warning("app.face_engine.degraded")

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

    _public_paths = {
        "/health",
        "/api/v1/auth/login",
        "/api/v1/gyms/public/onboarding",
    }

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        openapi_schema["components"]["securitySchemes"] = {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
        for path, methods in openapi_schema["paths"].items():
            if path not in _public_paths:
                for operation in methods.values():
                    operation.setdefault("security", [{"bearerAuth": []}])
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_v1_router)

    @app.get("/health", tags=["health"], summary="Health check")
    async def health() -> dict[str, str | bool]:
        face_engine: FaceEngine | None = getattr(app.state, "face_engine", None)
        return {
            "status": "ok",
            "environment": settings.environment,
            "face_engine_loaded": bool(face_engine and face_engine.is_loaded),
        }

    return app


app = create_app()
