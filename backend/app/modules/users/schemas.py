"""DTOs del módulo users."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Roles asignables a través de POST /gyms/{gym_id}/users.
# OWNER nunca: solo se asigna vía /gyms/public/onboarding o promoción manual.
GymAssignableRole = Literal["client", "manager"]


class UserCreateByGymMember(BaseModel):
    """Body para POST /gyms/{gym_id}/users.

    ``kind_role`` solo se respeta si el caller es OWNER del gym:
        - OWNER: puede crear CLIENT o MANAGER (default CLIENT).
        - MANAGER: siempre crea CLIENT; el campo se ignora silenciosamente.
    """

    email: EmailStr = Field(examples=["newmember@gym.com"])
    password: str = Field(min_length=8, max_length=128, examples=["strongpass123"])
    full_name: str = Field(min_length=2, max_length=255, examples=["Jane Doe"])
    kind_role: GymAssignableRole | None = Field(
        default=None,
        examples=["client"],
        description="Rol a asignar. Solo respetado si el caller es OWNER.",
    )


class UserCreatedResponse(BaseModel):
    id: uuid.UUID = Field(examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"])
    email: EmailStr = Field(examples=["newmember@gym.com"])
    full_name: str = Field(examples=["Jane Doe"])
    role: str = Field(examples=["client"])
    gym_id: uuid.UUID = Field(examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"])
    is_active: bool = True
    created_at: datetime = Field(examples=["2026-06-07T03:00:00Z"])

    model_config = ConfigDict(from_attributes=True)
