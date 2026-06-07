"""Endpoints de gestión de usuarios dentro de un gym.

POST   /gyms/{gym_id}/users — owner/manager del gym crea un usuario vinculado.
"""

import uuid

from fastapi import APIRouter, status

from app.core.dependencies import DbSession, GymManagerContext
from app.modules.gyms.service import get_gym
from app.modules.users import service
from app.modules.users.schemas import UserCreateByGymMember, UserCreatedResponse

router = APIRouter(prefix="/gyms", tags=["users"])


@router.post(
    "/{gym_id}/users",
    response_model=UserCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario en un gym (owner/manager)",
    description=(
        "Crea un usuario y lo vincula al gym con rol CLIENT o MANAGER. "
        "El campo `kind_role` solo se respeta si el caller es OWNER: "
        "OWNER puede crear CLIENT o MANAGER; MANAGER siempre crea CLIENT "
        "(el campo se ignora silenciosamente). "
        "Requiere rol manager o owner en el gym."
    ),
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
        kind_role=body.kind_role,
    )
    return UserCreatedResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_link.role.value,
        gym_id=gym.id,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
    )
