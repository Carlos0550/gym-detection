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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.api.v1 import api_v1_router
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()


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

    # Public endpoints que NO requieren auth
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

    @app.get(
        "/health",
        tags=["health"],
        summary="Health check",
        description="Endpoint de verificación. Devuelve estado OK y el entorno activo.",
    )
    async def health() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()
