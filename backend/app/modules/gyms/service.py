"""Lógica de gyms."""

import uuid

from app.core.security import create_access_token, hash_password
from app.core.logging import logger
from app.models.enums import GymUserRole
from app.modules.gyms.schemas import GymOnboardingRequest, GymOnboardingResponse
from app.utils.phone import to_e164
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.models.gym import Gym
from app.models.gym_user import GymUser
from app.models.user import User


async def list_gyms_for_user(db: AsyncSession, user: User) -> list[Gym]:
    """Gyms a los que el user tiene acceso (todos si es superadmin)."""
    if user.is_superadmin:
        result = await db.execute(
            select(Gym).where(Gym.is_active == True).order_by(Gym.name)  # noqa: E712
        )
        return list(result.scalars().all())

    result = await db.execute(
        select(Gym)
        .join(GymUser, GymUser.gym_id == Gym.id)
        .where(GymUser.user_id == user.id, Gym.is_active == True)  # noqa: E712
        .order_by(Gym.name)
    )
    return list(result.scalars().all())


async def list_all_gyms(db: AsyncSession) -> list[Gym]:
    result = await db.execute(select(Gym).order_by(Gym.created_at.desc()))
    return list(result.scalars().all())


async def create_gym(db: AsyncSession, *, name: str, address: str | None, phone: str | None) -> Gym:
    gym = Gym(name=name, address=address, phone=phone)
    db.add(gym)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ConflictError("No se pudo crear el gimnasio") from exc
    await db.refresh(gym)
    return gym

async def create_gym_onboarding(
    db: AsyncSession,
    request: GymOnboardingRequest
) -> GymOnboardingResponse:
    try:
        password_hash = hash_password(request.password)
        new_user = User(
            email=request.email.lower().strip(),
            password_hash=password_hash,
            full_name=request.operator_name.strip().lower(),
        )
        db.add(new_user)
        await db.flush()
        await db.refresh(new_user)
        new_gym = Gym(
            name=request.gym_name.strip().lower(),
            address=request.gym_address.strip().lower(),
            phone=to_e164(request.gym_phone),
        )
        db.add(new_gym)
        await db.flush()
        await db.refresh(new_gym)
        new_gym_user = GymUser(
            gym_id=new_gym.id,
            user_id=new_user.id,
            role=GymUserRole.OWNER,
        )
        db.add(new_gym_user)
        await db.commit()
        await db.refresh(new_gym_user)
        return GymOnboardingResponse(
            gym_name=new_gym.name,
            gym_address=new_gym.address,
            operator_name=new_user.full_name,
            operator_email=new_user.email,
            operator_access_token=create_access_token(new_user.id),
        )
    except Exception as e:
        logger.error("Error creating gym onboarding", error=e)
        await db.rollback()
        raise ConflictError("No se pudo crear el gimnasio") from e

async def get_gym(db: AsyncSession, gym_id: uuid.UUID) -> Gym:
    result = await db.execute(select(Gym).where(Gym.id == gym_id))
    gym = result.scalar_one_or_none()
    if gym is None:
        raise NotFoundError("Gimnasio no encontrado")
    return gym


async def update_gym(
    db: AsyncSession,
    gym: Gym,
    *,
    name: str | None = None,
    address: str | None = None,
    phone: str | None = None,
    is_active: bool | None = None,
) -> Gym:
    if name is not None:
        gym.name = name
    if address is not None:
        gym.address = address
    if phone is not None:
        gym.phone = phone
    if is_active is not None:
        gym.is_active = is_active
    await db.commit()
    await db.refresh(gym)
    return gym
