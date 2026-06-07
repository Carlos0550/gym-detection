"""Endpoints de gyms.

GET    /gyms                  — gyms a los que el user tiene acceso
POST   /gyms                  — crear (superadmin)
GET    /gyms/{gym_id}         — detalle (miembro con rol operator+)
PATCH  /gyms/{gym_id}         — editar (owner)
POST   /gyms/public/onboarding — onboarding (public) - Registra un usuario con rol OWNER y su primer gym
"""

import uuid

from fastapi import APIRouter, status

from app.core.dependencies import (
    CurrentUser,
    DbSession,
    GymContext,
    GymOwnerContext,
    Superadmin,
)
from app.modules.gyms import service
from app.modules.gyms.schemas import GymCreate, GymOnboardingRequest, GymOnboardingResponse, GymResponse, GymUpdate

router = APIRouter(prefix="/gyms", tags=["gyms"])


@router.get(
    "",
    response_model=list[GymResponse],
    summary="Listar gimnasios",
    description="Devuelve los gimnasios a los que el usuario autenticado tiene acceso. Los superadmins ven todos los gimnasios activos.",
)
async def list_gyms(user: CurrentUser, db: DbSession) -> list[GymResponse]:
    gyms = await service.list_gyms_for_user(db, user)
    return [GymResponse.model_validate(g) for g in gyms]


@router.post(
    "",
    response_model=GymResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear gimnasio (superadmin)",
    description="Crea un nuevo gimnasio. Solo accesible por superadmins.",
)
async def create_gym(
    body: GymCreate,
    db: DbSession,
    _: Superadmin,
) -> GymResponse:
    gym = await service.create_gym(
        db, name=body.name, address=body.address, phone=body.phone
    )
    return GymResponse.model_validate(gym)


@router.get(
    "/{gym_id}",
    response_model=GymResponse,
    summary="Detalle de gimnasio",
    description="Devuelve los datos de un gimnasio. Requiere ser miembro (cualquier rol) de ese gimnasio o superadmin.",
)
async def get_gym(
    gym_id: uuid.UUID,
    db: DbSession,
    _: GymContext,
) -> GymResponse:
    gym = await service.get_gym(db, gym_id)
    return GymResponse.model_validate(gym)


@router.patch(
    "/{gym_id}",
    response_model=GymResponse,
    summary="Actualizar gimnasio (owner)",
    description="Actualiza los datos de un gimnasio. Requiere rol OWNER en ese gimnasio o superadmin.",
)
async def update_gym_endpoint(
    gym_id: uuid.UUID,
    body: GymUpdate,
    db: DbSession,
    _: GymOwnerContext,
) -> GymResponse:
    gym = await service.get_gym(db, gym_id)
    updated = await service.update_gym(
        db,
        gym,
        name=body.name,
        address=body.address,
        phone=body.phone,
        is_active=body.is_active,
    )
    return GymResponse.model_validate(updated)


@router.post(
    "/public/onboarding",
    response_model=GymOnboardingResponse,
    summary="Onboarding público",
    description="Registra un nuevo usuario (rol OWNER) y su primer gimnasio en una sola transacción. Devuelve los datos del gimnasio creado y un access token para el operador.",
)
async def onboarding(
    body: GymOnboardingRequest,
    db: DbSession
) -> GymOnboardingResponse:
    new_gym = await service.create_gym_onboarding(
        db, body
    )
    await db.commit()
    return GymOnboardingResponse.model_validate(new_gym).model_dump()
