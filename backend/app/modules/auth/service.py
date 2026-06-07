"""Lógica de negocio de auth: login, register, me."""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User

settings = get_settings()


async def login(db: AsyncSession, email: str, password: str) -> tuple[User, str, int]:
    """Valida credenciales y devuelve ``(user, token, expires_in_seconds)``."""
    result = await db.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Credenciales inválidas")
    if not user.is_active:
        raise UnauthorizedError("Usuario inactivo")

    expires_minutes = settings.jwt_access_token_expires_minutes
    token = create_access_token(user.id, expires_minutes=expires_minutes)
    return user, token, expires_minutes * 60


async def register_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    full_name: str,
    is_superadmin: bool = False,
) -> User:
    """Crea un user nuevo. Email debe ser único."""
    user = User(
        id=uuid.uuid4(),
        email=email.lower(),
        password_hash=hash_password(password),
        full_name=full_name,
        is_superadmin=is_superadmin,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ConflictError("El email ya está registrado") from exc
    await db.refresh(user)
    return user
