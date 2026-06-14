"""Endpoints de verificación facial y access logs."""

import uuid

from fastapi import APIRouter, File, Query, UploadFile, status

from app.core.config import get_settings
from app.core.dependencies import DbSession, GymContext, GymManagerContext
from app.modules.access import service
from app.modules.access.schemas import AccessLogListResponse, AccessLogResponse, VerifyFaceResponse
from app.modules.face.dependencies import FaceEngineDep

router = APIRouter(prefix="/gyms", tags=["access"])
settings = get_settings()


@router.post(
    "/{gym_id}/access/verify-face",
    response_model=VerifyFaceResponse,
    status_code=status.HTTP_200_OK,
    summary="Verificar acceso por rostro (recepción)",
    description=(
        "Recibe al menos 2 frames para verificación de vivacidad. "
        "Requiere membresía activa para conceder acceso."
    ),
)
async def verify_face(
    gym_id: uuid.UUID,
    db: DbSession,
    _: GymContext,
    face_engine: FaceEngineDep,
    frames: list[UploadFile] = File(..., description="Frames JPEG/PNG/WEBP (mín. 2)"),
) -> VerifyFaceResponse:
    frame_bytes = [await frame.read() for frame in frames]
    result = await service.verify_face(
        db,
        settings=settings,
        face_engine=face_engine,
        gym_id=gym_id,
        frames=frame_bytes,
    )
    return VerifyFaceResponse.model_validate(result)


@router.get(
    "/{gym_id}/access/logs",
    response_model=AccessLogListResponse,
    summary="Listar access logs del gym",
)
async def list_access_logs(
    gym_id: uuid.UUID,
    db: DbSession,
    _: GymManagerContext,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> AccessLogListResponse:
    logs = await service.list_access_logs(db, gym_id, limit=limit, offset=offset)
    return AccessLogListResponse(
        items=[AccessLogResponse.model_validate(log) for log in logs],
        limit=limit,
        offset=offset,
    )
