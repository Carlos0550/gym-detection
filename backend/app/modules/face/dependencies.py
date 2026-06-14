"""Dependencia FastAPI para el motor facial."""

from typing import Annotated

from fastapi import Depends, Request

from app.core.exceptions import ServiceUnavailableError
from app.modules.face.engine import FaceEngine


def get_face_engine(request: Request) -> FaceEngine:
    """Devuelve el motor facial precargado en startup.

    Raises:
        ServiceUnavailableError: si el modelo no cargó (degraded mode).
    """
    engine: FaceEngine | None = getattr(request.app.state, "face_engine", None)
    if engine is None or not engine.is_loaded:
        raise ServiceUnavailableError(
            "El motor facial no está disponible. Intente más tarde."
        )
    return engine


FaceEngineDep = Annotated[FaceEngine, Depends(get_face_engine)]
