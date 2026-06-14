"""Lógica de enrolamiento facial."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import ConflictError, ForbiddenError
from app.models.enums import GymUserRole
from app.models.face_embedding import FaceEmbedding
from app.modules.face.engine import FaceEngine
from app.modules.face.liveness import LivenessFailedError
from app.modules.face.liveness_checker import LivenessChecker
from app.modules.face.pose_validator import (
    EnrollPoseStep,
    validate_enroll_pose,
    validate_guided_enroll_poses,
)
from app.modules.face.vector_search import find_duplicate_user_id
from app.modules.face.vector_utils import to_embedding_list
from app.modules.users.service import get_gym_user_link

MIN_ENROLL_FRAMES = 3


async def validate_enroll_pose_step(
    db: AsyncSession,
    *,
    gym_id: uuid.UUID,
    user_id: uuid.UUID,
    face_engine: FaceEngine,
    image_bytes: bytes,
    step: EnrollPoseStep,
) -> None:
    await get_gym_user_link(db, gym_id, user_id)
    faces = face_engine.detect_faces(image_bytes)
    if not faces:
        raise ConflictError("No se detectó rostro en la imagen")
    if len(faces) > 1:
        raise ConflictError("Se detectaron múltiples rostros; solo debe haber uno")
    try:
        validate_enroll_pose(faces[0], step)
    except LivenessFailedError as exc:
        raise ConflictError(str(exc)) from exc


async def enroll_face(
    db: AsyncSession,
    *,
    settings: Settings,
    face_engine: FaceEngine,
    gym_id: uuid.UUID,
    user_id: uuid.UUID,
    frames: list[bytes],
) -> FaceEmbedding:
    _user, link = await get_gym_user_link(db, gym_id, user_id)

    if link.role != GymUserRole.CLIENT:
        raise ForbiddenError("Solo clientes pueden enrolar rostro")

    if link.biometric_consent_at is None:
        raise ForbiddenError(
            "Consentimiento biométrico requerido antes del enrolamiento"
        )

    if len(frames) < MIN_ENROLL_FRAMES:
        raise ConflictError(
            f"Se requieren al menos {MIN_ENROLL_FRAMES} frames "
            "(centro, izquierda, derecha)"
        )

    checker = LivenessChecker()
    try:
        detections = checker.detect_all(face_engine, frames)
        validate_guided_enroll_poses(detections)
        detection = checker.verify_guided_enroll_detections(face_engine, detections)
    except LivenessFailedError as exc:
        raise ConflictError(str(exc)) from exc

    embedding = detection.embedding

    duplicate_user_id = await find_duplicate_user_id(
        db,
        gym_id=gym_id,
        embedding=embedding,
        exclude_user_id=user_id,
        threshold=settings.face_threshold_duplicate,
        face_engine=face_engine,
    )
    if duplicate_user_id is not None:
        raise ConflictError(
            "El rostro ya está registrado para otro usuario de este gimnasio"
        )

    existing = await db.execute(
        select(FaceEmbedding).where(
            FaceEmbedding.gym_id == gym_id, FaceEmbedding.user_id == user_id
        )
    )
    for row in existing.scalars().all():
        await db.delete(row)

    record = FaceEmbedding(
        gym_id=gym_id,
        user_id=user_id,
        embedding=to_embedding_list(embedding),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_user_embeddings(
    db: AsyncSession, gym_id: uuid.UUID, user_id: uuid.UUID
) -> list[FaceEmbedding]:
    await get_gym_user_link(db, gym_id, user_id)
    result = await db.execute(
        select(FaceEmbedding)
        .where(FaceEmbedding.gym_id == gym_id, FaceEmbedding.user_id == user_id)
        .order_by(FaceEmbedding.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_user_embeddings(
    db: AsyncSession, gym_id: uuid.UUID, user_id: uuid.UUID
) -> int:
    await get_gym_user_link(db, gym_id, user_id)
    result = await db.execute(
        select(FaceEmbedding).where(
            FaceEmbedding.gym_id == gym_id, FaceEmbedding.user_id == user_id
        )
    )
    rows = list(result.scalars().all())
    for row in rows:
        await db.delete(row)
    await db.commit()
    return len(rows)
