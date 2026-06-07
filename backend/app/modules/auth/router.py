"""Endpoints de autenticación: login, register, me."""

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, DbSession, Superadmin
from app.modules.auth import service
from app.modules.auth.schemas import (
    LoginRequest,
    MeResponse,
    RegisterRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: DbSession) -> TokenResponse:
    user, token, expires_in = await service.login(db, body.email, body.password)
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.post(
    "/register",
    response_model=MeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    db: DbSession,
    _: Superadmin,
) -> MeResponse:
    user = await service.register_user(
        db,
        email=body.email,
        password=body.password,
        full_name=body.full_name,
        is_superadmin=body.is_superadmin,
    )
    return MeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_superadmin=user.is_superadmin,
        is_active=user.is_active,
        created_at=user.created_at,
        memberships=[],
    )


@router.get("/me", response_model=MeResponse)
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
