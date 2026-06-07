"""Lógica de gyms."""

import uuid

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
