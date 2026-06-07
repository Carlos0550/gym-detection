"""Hashing de passwords y JWT.

Usa argon2 vía passlib (sin límite de 72 bytes que tiene bcrypt) y
python-jose para JWT.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

_pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _pwd_context.verify(plain, hashed)
    except (ValueError, TypeError):
        return False


def create_access_token(
    subject: str | uuid.UUID,
    extra_claims: dict[str, Any] | None = None,
    expires_minutes: int | None = None,
) -> str:
    """Genera un JWT firmado. ``subject`` es el user id (string o UUID)."""
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes or settings.jwt_access_token_expires_minutes)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodifica y valida el JWT. Raises ``jose.JWTError`` si es inválido o expiró."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "JWTError",
]
