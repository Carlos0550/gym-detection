"""Lógica de verificación facial y access logs."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings
from app.core.exceptions import ConflictError
from app.models.access_log import AccessLog
from app.models.enums import AccessResult, MembershipStatus, is_membership_active
from app.models.gym_user import GymUser
from app.models.membership import Membership
from app.models.user import User
from app.modules.face.engine import FaceEngine
from app.modules.face.liveness_checker import LivenessChecker
from app.modules.face.liveness import LivenessFailedError
from app.modules.face.vector_search import find_best_match


async def get_active_membership(
    db: AsyncSession, gym_user_id: uuid.UUID, *, on_date: date | None = None
) -> Membership | None:
    result = await db.execute(
        select(Membership)
        .where(Membership.gym_user_id == gym_user_id)
        .order_by(Membership.start_date.desc())
    )
    for membership in result.scalars().all():
        if is_membership_active(
            membership.status, membership.start_date, membership.end_date, on_date=on_date
        ):
            return membership
    return None


async def _write_access_log(
    db: AsyncSession,
    *,
    gym_id: uuid.UUID,
    user_id: uuid.UUID | None,
    result: AccessResult,
    confidence: float | None,
    membership_status: str | None,
    detail: str | None = None,
) -> AccessLog:
    log = AccessLog(
        gym_id=gym_id,
        user_id=user_id,
        result=result,
        confidence=confidence,
        membership_status=membership_status,
        detail=detail,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def verify_face(
    db: AsyncSession,
    *,
    settings: Settings,
    face_engine: FaceEngine,
    gym_id: uuid.UUID,
    frames: list[bytes],
) -> dict:
    liveness = LivenessChecker()
    try:
        detection = liveness.verify(face_engine, frames)
    except LivenessFailedError as exc:
        log = await _write_access_log(
            db,
            gym_id=gym_id,
            user_id=None,
            result=AccessResult.DENIED,
            confidence=None,
            membership_status=None,
            detail=str(exc),
        )
        return {
            "matched": False,
            "confidence": None,
            "result": AccessResult.DENIED.value,
            "access": "denied",
            "reason": str(exc),
            "log_id": log.id,
        }

    embedding = detection.embedding
    match = await find_best_match(
        db, gym_id=gym_id, embedding=embedding, face_engine=face_engine
    )

    if match is None:
        log = await _write_access_log(
            db,
            gym_id=gym_id,
            user_id=None,
            result=AccessResult.UNKNOWN,
            confidence=None,
            membership_status=None,
            detail="Sin embeddings en el gimnasio",
        )
        return {
            "matched": False,
            "confidence": None,
            "result": AccessResult.UNKNOWN.value,
            "access": "denied",
            "reason": "Rostro no reconocido",
            "log_id": log.id,
        }

    face_row, matched_user, confidence = match

    if confidence < settings.face_threshold_low:
        log = await _write_access_log(
            db,
            gym_id=gym_id,
            user_id=None,
            result=AccessResult.UNKNOWN,
            confidence=confidence,
            membership_status=None,
        )
        return {
            "matched": False,
            "confidence": confidence,
            "result": AccessResult.UNKNOWN.value,
            "access": "denied",
            "reason": "Rostro no reconocido",
            "log_id": log.id,
        }

    link_result = await db.execute(
        select(GymUser)
        .options(selectinload(GymUser.memberships))
        .where(GymUser.gym_id == gym_id, GymUser.user_id == matched_user.id)
    )
    gym_user = link_result.scalar_one_or_none()

    membership = (
        await get_active_membership(db, gym_user.id) if gym_user is not None else None
    )
    membership_payload = None
    if membership is not None:
        membership_payload = {
            "id": membership.id,
            "status": membership.status.value,
            "start_date": membership.start_date.isoformat(),
            "end_date": membership.end_date.isoformat() if membership.end_date else None,
        }

    user_payload = {
        "id": matched_user.id,
        "full_name": matched_user.full_name,
        "document": gym_user.document if gym_user is not None else None,
        "email": matched_user.email,
    }

    if confidence < settings.face_threshold_match:
        log = await _write_access_log(
            db,
            gym_id=gym_id,
            user_id=matched_user.id,
            result=AccessResult.LOW_CONFIDENCE,
            confidence=confidence,
            membership_status=membership.status.value if membership else None,
        )
        return {
            "matched": True,
            "confidence": confidence,
            "result": AccessResult.LOW_CONFIDENCE.value,
            "access": "denied",
            "user": user_payload,
            "membership": membership_payload,
            "reason": "Confianza insuficiente",
            "log_id": log.id,
        }

    if membership is None:
        log = await _write_access_log(
            db,
            gym_id=gym_id,
            user_id=matched_user.id,
            result=AccessResult.DENIED,
            confidence=confidence,
            membership_status="inactive",
            detail="Membresía no vigente",
        )
        return {
            "matched": True,
            "confidence": confidence,
            "result": AccessResult.DENIED.value,
            "access": "denied",
            "user": user_payload,
            "membership": membership_payload,
            "reason": "Membresía no vigente",
            "log_id": log.id,
        }

    log = await _write_access_log(
        db,
        gym_id=gym_id,
        user_id=matched_user.id,
        result=AccessResult.GRANTED,
        confidence=confidence,
        membership_status=membership.status.value,
    )
    return {
        "matched": True,
        "confidence": confidence,
        "result": AccessResult.GRANTED.value,
        "access": "granted",
        "user": user_payload,
        "membership": membership_payload,
        "log_id": log.id,
    }


async def list_access_logs(
    db: AsyncSession,
    gym_id: uuid.UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    result = await db.execute(
        select(AccessLog, User, GymUser)
        .outerjoin(User, User.id == AccessLog.user_id)
        .outerjoin(
            GymUser,
            (GymUser.user_id == AccessLog.user_id) & (GymUser.gym_id == AccessLog.gym_id),
        )
        .where(AccessLog.gym_id == gym_id)
        .order_by(AccessLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows: list[dict] = []
    for log, user, gym_user in result.all():
        rows.append(
            {
                "id": log.id,
                "gym_id": log.gym_id,
                "user_id": log.user_id,
                "user_full_name": user.full_name if user is not None else None,
                "user_document": gym_user.document if gym_user is not None else None,
                "result": log.result.value,
                "confidence": log.confidence,
                "membership_status": log.membership_status,
                "detail": log.detail,
                "created_at": log.created_at,
            }
        )
    return rows
