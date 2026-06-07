"""Endpoints de gyms.

GET    /gyms                  — gyms a los que el user tiene acceso
POST   /gyms                  — crear (superadmin)
GET    /gyms/{gym_id}         — detalle (miembro con rol operator+)
PATCH  /gyms/{gym_id}         — editar (owner)
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
from app.modules.gyms.schemas import GymCreate, GymResponse, GymUpdate

router = APIRouter(prefix="/gyms", tags=["gyms"])


@router.get("", response_model=list[GymResponse])
async def list_gyms(user: CurrentUser, db: DbSession) -> list[GymResponse]:
    gyms = await service.list_gyms_for_user(db, user)
    return [GymResponse.model_validate(g) for g in gyms]


@router.post("", response_model=GymResponse, status_code=status.HTTP_201_CREATED)
async def create_gym(
    body: GymCreate,
    db: DbSession,
    _: Superadmin,
) -> GymResponse:
    gym = await service.create_gym(
        db, name=body.name, address=body.address, phone=body.phone
    )
    return GymResponse.model_validate(gym)


@router.patch("/{gym_id}", response_model=GymResponse)
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
