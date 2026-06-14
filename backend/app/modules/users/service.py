"""Lógica de users: alta y gestión de clientes dentro de un gym."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.models.enums import GymUserRole, is_membership_active
from app.models.membership import Membership
from app.models.gym import Gym
from app.models.gym_user import GymUser
from app.models.user import User


def resolve_role_for_caller(
    caller_role: GymUserRole,
    kind_role: str | None,
) -> GymUserRole:
    if caller_role == GymUserRole.OWNER and kind_role is not None:
        return GymUserRole(kind_role)
    return GymUserRole.CLIENT


def _normalize_document(document: str | None) -> str | None:
    if document is None:
        return None
    cleaned = document.strip()
    return cleaned or None


async def create_user_for_gym(
    db: AsyncSession,
    *,
    gym: Gym,
    caller_role: GymUserRole,
    email: str,
    password: str,
    full_name: str,
    document: str | None = None,
    kind_role: str | None = None,
) -> tuple[User, GymUser]:
    role = resolve_role_for_caller(caller_role, kind_role)
    normalized_document = _normalize_document(document)

    if role == GymUserRole.CLIENT and not normalized_document:
        raise ConflictError("El documento (DNI) es obligatorio para clientes")

    new_user = User(
        id=uuid.uuid4(),
        email=email.lower().strip(),
        password_hash=hash_password(password),
        full_name=full_name.strip(),
        is_superadmin=False,
    )
    db.add(new_user)

    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise ConflictError("El email ya está registrado") from exc

    new_link = GymUser(
        gym_id=gym.id,
        user_id=new_user.id,
        role=role,
        document=normalized_document,
    )
    db.add(new_link)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ConflictError(
            "El documento ya está registrado en este gimnasio"
        ) from exc

    await db.refresh(new_user)
    await db.refresh(new_link)
    return new_user, new_link


def pick_active_membership(memberships: list[Membership]) -> Membership | None:
    for membership in sorted(memberships, key=lambda row: row.start_date, reverse=True):
        if is_membership_active(
            membership.status, membership.start_date, membership.end_date
        ):
            return membership
    return None


async def list_gym_clients(
    db: AsyncSession, gym_id: uuid.UUID
) -> list[tuple[User, GymUser, Membership | None]]:
    result = await db.execute(
        select(User, GymUser)
        .join(GymUser, GymUser.user_id == User.id)
        .where(GymUser.gym_id == gym_id, GymUser.role == GymUserRole.CLIENT)
        .options(selectinload(GymUser.memberships))
        .order_by(User.full_name)
    )
    rows: list[tuple[User, GymUser, Membership | None]] = []
    for user, link in result.all():
        rows.append((user, link, pick_active_membership(link.memberships)))
    return rows


async def get_gym_user_link(
    db: AsyncSession, gym_id: uuid.UUID, user_id: uuid.UUID
) -> tuple[User, GymUser]:
    result = await db.execute(
        select(User, GymUser)
        .join(GymUser, GymUser.user_id == User.id)
        .where(GymUser.gym_id == gym_id, GymUser.user_id == user_id)
    )
    row = result.first()
    if row is None:
        raise NotFoundError("Usuario no encontrado en este gimnasio")
    return row[0], row[1]


async def update_gym_user(
    db: AsyncSession,
    *,
    gym_id: uuid.UUID,
    user_id: uuid.UUID,
    document: str | None = None,
    grant_biometric_consent: bool | None = None,
) -> tuple[User, GymUser]:
    user, link = await get_gym_user_link(db, gym_id, user_id)

    if document is not None:
        link.document = _normalize_document(document)

    if grant_biometric_consent is True:
        link.biometric_consent_at = datetime.now(timezone.utc)
    elif grant_biometric_consent is False:
        link.biometric_consent_at = None

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ConflictError(
            "El documento ya está registrado en este gimnasio"
        ) from exc

    await db.refresh(user)
    await db.refresh(link)
    return user, link
