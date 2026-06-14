"""Endpoints de gestión de usuarios dentro de un gym."""

import uuid

from fastapi import APIRouter, status

from app.core.dependencies import DbSession, GymManagerContext
from app.modules.gyms.service import get_gym
from app.modules.users import service
from app.modules.users.schemas import (
    ActiveMembershipSummary,
    GymClientResponse,
    GymUserUpdate,
    UserCreateByGymMember,
    UserCreatedResponse,
)

router = APIRouter(prefix="/gyms", tags=["users"])


def _created_response(
    user, link, gym_id: uuid.UUID
) -> UserCreatedResponse:
    return UserCreatedResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        document=link.document,
        role=link.role.value,
        gym_id=gym_id,
        is_active=user.is_active,
        biometric_consent_at=link.biometric_consent_at,
        created_at=user.created_at,
    )


def _membership_summary(membership) -> ActiveMembershipSummary | None:
    if membership is None:
        return None
    return ActiveMembershipSummary(
        id=membership.id,
        status=membership.status.value,
        start_date=membership.start_date,
        end_date=membership.end_date,
    )


def _client_response(
    user, link, gym_id: uuid.UUID, active_membership=None
) -> GymClientResponse:
    return GymClientResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        document=link.document,
        role=link.role.value,
        gym_id=gym_id,
        is_active=user.is_active,
        biometric_consent_at=link.biometric_consent_at,
        active_membership=_membership_summary(active_membership),
        created_at=link.created_at,
    )


@router.get(
    "/{gym_id}/users",
    response_model=list[GymClientResponse],
    summary="Listar clientes del gym",
)
async def list_gym_clients(
    gym_id: uuid.UUID,
    db: DbSession,
    _: GymManagerContext,
) -> list[GymClientResponse]:
    rows = await service.list_gym_clients(db, gym_id)
    return [
        _client_response(user, link, gym_id, active_membership)
        for user, link, active_membership in rows
    ]


@router.post(
    "/{gym_id}/users",
    response_model=UserCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario en un gym (owner/manager)",
)
async def create_gym_user(
    gym_id: uuid.UUID,
    body: UserCreateByGymMember,
    db: DbSession,
    ctx: GymManagerContext,
) -> UserCreatedResponse:
    _user, caller_link = ctx
    gym = await get_gym(db, gym_id)

    new_user, new_link = await service.create_user_for_gym(
        db,
        gym=gym,
        caller_role=caller_link.role,
        email=body.email,
        password=body.password,
        full_name=body.full_name,
        document=body.document,
        kind_role=body.kind_role,
    )
    return _created_response(new_user, new_link, gym.id)


@router.patch(
    "/{gym_id}/users/{user_id}",
    response_model=GymClientResponse,
    summary="Actualizar cliente (documento, consentimiento biométrico)",
)
async def update_gym_user(
    gym_id: uuid.UUID,
    user_id: uuid.UUID,
    body: GymUserUpdate,
    db: DbSession,
    _: GymManagerContext,
) -> GymClientResponse:
    user, link = await service.update_gym_user(
        db,
        gym_id=gym_id,
        user_id=user_id,
        document=body.document,
        grant_biometric_consent=body.grant_biometric_consent,
    )
    return _client_response(user, link, gym_id)
