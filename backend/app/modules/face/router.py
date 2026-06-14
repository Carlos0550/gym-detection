"""Endpoints de enrolamiento facial."""

import uuid

from fastapi import APIRouter, File, Form, UploadFile, status

from app.core.config import get_settings
from app.core.dependencies import DbSession, GymManagerContext
from app.modules.face.dependencies import FaceEngineDep
from app.modules.face.enroll_schemas import (
    FaceDeleteResponse,
    FaceEmbeddingResponse,
    FaceEnrollResponse,
    PoseValidationResponse,
)
from app.modules.face import service
from app.modules.face.pose_validator import EnrollPoseStep

router = APIRouter(prefix="/gyms", tags=["face"])
settings = get_settings()


@router.post(
    "/{gym_id}/users/{user_id}/face/enroll",
    response_model=FaceEnrollResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enrolar rostro de un cliente",
    description=(
        "Recibe al menos 3 frames guiados (centro, giro izquierda, giro derecha) "
        "con verificación de vivacidad antes de guardar el embedding."
    ),
)
async def enroll_face(
    gym_id: uuid.UUID,
    user_id: uuid.UUID,
    db: DbSession,
    _: GymManagerContext,
    face_engine: FaceEngineDep,
    frames: list[UploadFile] = File(
        ..., description="Frames JPEG/PNG/WEBP (mín. 3, con movimiento de cabeza)"
    ),
) -> FaceEnrollResponse:
    frame_bytes = [await frame.read() for frame in frames]
    record = await service.enroll_face(
        db,
        settings=settings,
        face_engine=face_engine,
        gym_id=gym_id,
        user_id=user_id,
        frames=frame_bytes,
    )
    return FaceEnrollResponse.model_validate(record)


@router.post(
    "/{gym_id}/users/{user_id}/face/enroll/validate-pose",
    response_model=PoseValidationResponse,
    summary="Validar pose de un paso del enrolamiento guiado",
)
async def validate_enroll_pose_step(
    gym_id: uuid.UUID,
    user_id: uuid.UUID,
    db: DbSession,
    _: GymManagerContext,
    face_engine: FaceEngineDep,
    step: EnrollPoseStep = Form(..., description="center | left | right"),
    image: UploadFile = File(..., description="Frame JPEG/PNG/WEBP"),
) -> PoseValidationResponse:
    image_bytes = await image.read()
    await service.validate_enroll_pose_step(
        db,
        gym_id=gym_id,
        user_id=user_id,
        face_engine=face_engine,
        image_bytes=image_bytes,
        step=step,
    )
    return PoseValidationResponse(ok=True)


@router.get(
    "/{gym_id}/users/{user_id}/face",
    response_model=list[FaceEmbeddingResponse],
    summary="Listar embeddings faciales de un usuario",
)
async def list_face_embeddings(
    gym_id: uuid.UUID,
    user_id: uuid.UUID,
    db: DbSession,
    _: GymManagerContext,
) -> list[FaceEmbeddingResponse]:
    rows = await service.get_user_embeddings(db, gym_id, user_id)
    return [FaceEmbeddingResponse.model_validate(row) for row in rows]


@router.delete(
    "/{gym_id}/users/{user_id}/face",
    response_model=FaceDeleteResponse,
    summary="Eliminar embeddings faciales de un usuario",
)
async def delete_face_embeddings(
    gym_id: uuid.UUID,
    user_id: uuid.UUID,
    db: DbSession,
    _: GymManagerContext,
) -> FaceDeleteResponse:
    deleted = await service.delete_user_embeddings(db, gym_id, user_id)
    return FaceDeleteResponse(deleted=deleted)
