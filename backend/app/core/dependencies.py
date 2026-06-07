"""Dependencias compartidas de FastAPI: auth, RBAC, sesión de DB.

Jerarquía de roles (en el módulo `app.models.enums`):
    client < manager < owner
"""

import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import JWTError, decode_access_token
from app.models.enums import GymUserRole, has_at_least
from app.models.gym_user import GymUser
from app.models.user import User

settings = get_settings()


# ============================================================
# DB session
# ============================================================
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


DbSession = Annotated[AsyncSession, Depends(get_db)]


# ============================================================
# Auth
# ============================================================
async def get_current_user(
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    """Extrae el usuario del JWT en el header Authorization: Bearer <token>."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("Token de autenticación requerido")

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
    except JWTError as exc:
        raise UnauthorizedError(f"Token inválido: {exc}") from exc

    if not sub:
        raise UnauthorizedError("Token inválido: falta subject")

    try:
        user_id = uuid.UUID(sub)
    except ValueError as exc:
        raise UnauthorizedError("Token inválido: subject no es UUID") from exc

    result = await db.execute(
        select(User)
        .options(selectinload(User.gym_memberships).selectinload(GymUser.gym))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedError("Usuario no encontrado")
    if not user.is_active:
        raise UnauthorizedError("Usuario inactivo")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


# ============================================================
# RBAC
# ============================================================
async def require_superadmin(user: CurrentUser) -> User:
    """Solo accesible para superadmins globales del sistema."""
    if not user.is_superadmin:
        raise ForbiddenError("Requiere permisos de superadmin")
    return user


Superadmin = Annotated[User, Depends(require_superadmin)]


class GymRoleChecker:
    """Dependencia de clase para validar que el user tenga al menos ``min_role``
    en el gym cuyo id viene en el path.

    Uso en routers:
        @router.get("/gyms/{gym_id}/...")
        async def handler(
            _: Annotated[tuple[User, GymUser], Depends(GymRoleChecker(GymUserRole.MANAGER))],
            ...
        ):
    """

    def __init__(self, min_role: GymUserRole = GymUserRole.CLIENT) -> None:
        self.min_role = min_role

    async def __call__(
        self,
        gym_id: Annotated[uuid.UUID, Path(...)],
        user: CurrentUser,
    ) -> tuple[User, GymUser]:
        if user.is_superadmin:
            virtual = GymUser(
                gym_id=gym_id, user_id=user.id, role=GymUserRole.OWNER
            )
            return user, virtual

        for link in user.gym_memberships:
            if link.gym_id == gym_id and has_at_least(link.role, self.min_role):
                return user, link

        raise ForbiddenError(
            f"Sin rol {self.min_role.value} en este gimnasio"
        )


GymContext = Annotated[tuple[User, GymUser], Depends(GymRoleChecker())]
GymManagerContext = Annotated[tuple[User, GymUser], Depends(GymRoleChecker(GymUserRole.MANAGER))]
GymOwnerContext = Annotated[tuple[User, GymUser], Depends(GymRoleChecker(GymUserRole.OWNER))]


__all__ = [
    "DbSession",
    "CurrentUser",
    "Superadmin",
    "GymRoleChecker",
    "GymContext",
    "GymManagerContext",
    "GymOwnerContext",
    "get_current_user",
    "require_superadmin",
]
