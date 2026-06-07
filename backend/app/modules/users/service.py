"""Lógica de users: alta de usuarios dentro de un gym."""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.core.security import hash_password
from app.models.enums import GymUserRole
from app.models.gym import Gym
from app.models.gym_user import GymUser
from app.models.user import User


def resolve_role_for_caller(
    caller_role: GymUserRole,
    kind_role: str | None,
) -> GymUserRole:
    """Resuelve el rol a asignar al nuevo user.

    - OWNER: respeta ``kind_role`` (default CLIENT).
    - MANAGER: siempre CLIENT, ignora ``kind_role``.
    """
    if caller_role == GymUserRole.OWNER and kind_role is not None:
        return GymUserRole(kind_role)
    return GymUserRole.CLIENT


async def create_user_for_gym(
    db: AsyncSession,
    *,
    gym: Gym,
    caller_role: GymUserRole,
    email: str,
    password: str,
    full_name: str,
    kind_role: str | None = None,
) -> tuple[User, GymUser]:
    """Crea un User y lo vincula al gym con el rol resuelto.

    Atómico: si falla el vínculo o el email está duplicado, se hace rollback
    completo (no queda User huérfano).
    """
    role = resolve_role_for_caller(caller_role, kind_role)

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
    )
    db.add(new_link)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ConflictError("No se pudo vincular el usuario al gimnasio") from exc

    await db.refresh(new_user)
    return new_user, new_link
