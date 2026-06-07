"""Seed inicial: crea superadmin + gym de demo + asigna rol owner al superadmin.

Uso:
    docker compose exec backend python -m app.seed

Idempotente: si los datos ya existen, los deja como están.
"""

import asyncio

import structlog
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.enums import GymUserRole
from app.models.gym import Gym
from app.models.gym_user import GymUser
from app.models.user import User

logger = structlog.get_logger()
settings = get_settings()


async def _get_or_create_superadmin(db) -> User:
    result = await db.execute(
        select(User).where(User.email == settings.seed_superadmin_email.lower())
    )
    user = result.scalar_one_or_none()
    if user is not None:
        logger.info("seed.superadmin_exists", email=user.email)
        return user

    user = User(
        email=settings.seed_superadmin_email.lower(),
        password_hash=hash_password(settings.seed_superadmin_password),
        full_name=settings.seed_superadmin_name,
        is_superadmin=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("seed.superadmin_created", email=user.email)
    return user


async def _get_or_create_demo_gym(db) -> Gym:
    result = await db.execute(select(Gym).where(Gym.name == settings.seed_gym_name))
    gym = result.scalar_one_or_none()
    if gym is not None:
        logger.info("seed.gym_exists", name=gym.name)
        return gym

    gym = Gym(
        name=settings.seed_gym_name,
        address=settings.seed_gym_address,
        phone=settings.seed_gym_phone,
    )
    db.add(gym)
    await db.commit()
    await db.refresh(gym)
    logger.info("seed.gym_created", name=gym.name)
    return gym


async def _link_owner(db, user: User, gym: Gym) -> None:
    result = await db.execute(
        select(GymUser).where(
            GymUser.gym_id == gym.id, GymUser.user_id == user.id
        )
    )
    link = result.scalar_one_or_none()
    if link is not None:
        logger.info("seed.owner_link_exists")
        return

    link = GymUser(gym_id=gym.id, user_id=user.id, role=GymUserRole.OWNER)
    db.add(link)
    await db.commit()
    logger.info("seed.owner_link_created")


async def main() -> None:
    logger.info("seed.start")
    async with AsyncSessionLocal() as db:
        user = await _get_or_create_superadmin(db)
        gym = await _get_or_create_demo_gym(db)
        await _link_owner(db, user, gym)
    logger.info(
        "seed.done",
        superadmin_email=user.email,
        gym_name=gym.name,
        message=(
            "Login con las credenciales del .env. Cambiá la contraseña en "
            "producción."
        ),
    )


if __name__ == "__main__":
    asyncio.run(main())
