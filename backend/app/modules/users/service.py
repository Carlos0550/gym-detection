"""Lógica de users: alta y gestión de clientes dentro de un gym."""

from __future__ import annotations

import secrets
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


def _normalize_email(email: str | None) -> str | None:
    if email is None:
        return None
    cleaned = email.strip().lower()
    return cleaned or None


def generate_temporary_password() -> str:
    return secrets.token_urlsafe(12)


def _placeholder_email() -> str:
    return f"noemail+{uuid.uuid4()}@gym-detection.internal"


async def _get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def _get_gym_user_link_for_user(
    db: AsyncSession, gym_id: uuid.UUID, user_id: uuid.UUID
) -> GymUser | None:
    result = await db.execute(
        select(GymUser).where(GymUser.gym_id == gym_id, GymUser.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def _link_existing_user_to_gym(
    db: AsyncSession,
    *,
    gym: Gym,
    user: User,
    role: GymUserRole,
    document: str | None,
) -> GymUser:
    new_link = GymUser(
        gym_id=gym.id,
        user_id=user.id,
        role=role,
        document=document,
    )
    db.add(new_link)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ConflictError(
            "El documento ya está registrado en este gimnasio"
        ) from exc
    await db.refresh(user)
    await db.refresh(new_link)
    return new_link


async def create_user_for_gym(
    db: AsyncSession,
    *,
    gym: Gym,
    caller_role: GymUserRole,
    email: str | None,
    password: str | None,
    full_name: str,
    document: str | None = None,
    kind_role: str | None = None,
) -> tuple[User, GymUser, str | None]:
    role = resolve_role_for_caller(caller_role, kind_role)
    normalized_document = _normalize_document(document)
    normalized_email = _normalize_email(email)

    if not normalized_email and not normalized_document:
        raise ConflictError("Ingresá email o DNI para identificar al miembro")

    if normalized_email:
        existing_user = await _get_user_by_email(db, normalized_email)
        if existing_user is not None:
            if await _get_gym_user_link_for_user(db, gym.id, existing_user.id) is not None:
                raise ConflictError("Este email ya está registrado en este gimnasio")
            new_link = await _link_existing_user_to_gym(
                db,
                gym=gym,
                user=existing_user,
                role=role,
                document=normalized_document,
            )
            return existing_user, new_link, None

    resolved_email = normalized_email or _placeholder_email()
    generated_password: str | None = None
    if password is None:
        password = generate_temporary_password()
        generated_password = password

    new_user = User(
        id=uuid.uuid4(),
        email=resolved_email,
        password_hash=hash_password(password),
        full_name=full_name.strip(),
        is_superadmin=False,
    )
    db.add(new_user)

    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise ConflictError("Este email ya está registrado en este gimnasio") from exc

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
    return new_user, new_link, generated_password


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
