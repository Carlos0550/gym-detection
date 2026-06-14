"""Búsqueda de similitud facial en Python (MVP, sin operadores pgvector en SQL)."""

from __future__ import annotations

import uuid

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.face_embedding import FaceEmbedding
from app.models.user import User
from app.modules.face.engine import FaceEngine


async def find_best_match(
    db: AsyncSession,
    *,
    gym_id: uuid.UUID,
    embedding: np.ndarray,
    face_engine: FaceEngine,
) -> tuple[FaceEmbedding, User, float] | None:
    stmt = (
        select(FaceEmbedding, User)
        .join(User, User.id == FaceEmbedding.user_id)
        .where(FaceEmbedding.gym_id == gym_id)
    )
    result = await db.execute(stmt)

    best: tuple[FaceEmbedding, User, float] | None = None
    for face_row, user in result.all():
        stored = np.asarray(face_row.embedding, dtype=np.float32)
        confidence = face_engine.compute_similarity(stored, embedding)
        if best is None or confidence > best[2]:
            best = (face_row, user, confidence)
    return best


async def find_duplicate_user_id(
    db: AsyncSession,
    *,
    gym_id: uuid.UUID,
    embedding: np.ndarray,
    exclude_user_id: uuid.UUID | None,
    threshold: float,
    face_engine: FaceEngine,
) -> uuid.UUID | None:
    stmt = select(FaceEmbedding).where(FaceEmbedding.gym_id == gym_id)
    if exclude_user_id is not None:
        stmt = stmt.where(FaceEmbedding.user_id != exclude_user_id)

    result = await db.execute(stmt)
    for row in result.scalars().all():
        stored = np.asarray(row.embedding, dtype=np.float32)
        if face_engine.compute_similarity(stored, embedding) >= threshold:
            return row.user_id
    return None
