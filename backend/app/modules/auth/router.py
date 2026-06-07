"""Endpoints de autenticación: login, me."""

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.modules.auth import service
from app.modules.auth.schemas import (
    LoginRequest,
    MeResponse,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
    description="Valida credenciales (email + password) y devuelve un JWT access token.",
)
async def login(body: LoginRequest, db: DbSession) -> TokenResponse:
    user, token, expires_in = await service.login(db, body.email, body.password)
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Perfil del usuario autenticado",
    description="Devuelve los datos del usuario junto con sus membresías activas por gimnasio.",
)
async def me(user: CurrentUser) -> MeResponse:
    return MeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_superadmin=user.is_superadmin,
        is_active=user.is_active,
        created_at=user.created_at,
        memberships=[
            {
                "gym_id": m.gym_id,
                "gym_name": m.gym.name,
                "role": m.role.value,
            }
            for m in user.gym_memberships
        ],
    )
