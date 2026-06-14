"""Endpoints de membresías."""

import uuid

from fastapi import APIRouter, status

from app.core.dependencies import DbSession, GymManagerContext
from app.modules.memberships import service
from app.modules.memberships.schemas import MembershipCreate, MembershipResponse

router = APIRouter(prefix="/gyms", tags=["memberships"])


@router.post(
    "/{gym_id}/users/{user_id}/memberships",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear membresía para un cliente",
)
async def create_membership(
    gym_id: uuid.UUID,
    user_id: uuid.UUID,
    body: MembershipCreate,
    db: DbSession,
    _: GymManagerContext,
) -> MembershipResponse:
    membership = await service.create_membership(
        db,
        gym_id=gym_id,
        user_id=user_id,
        start_date=body.start_date,
        end_date=body.end_date,
    )
    return MembershipResponse.model_validate(membership)
