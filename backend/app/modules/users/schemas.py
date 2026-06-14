"""DTOs del módulo users."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


GymAssignableRole = Literal["client", "manager"]


class ActiveMembershipSummary(BaseModel):
    id: uuid.UUID
    status: str
    start_date: date
    end_date: date | None = None


class UserCreateByGymMember(BaseModel):
    email: EmailStr = Field(examples=["newmember@gym.com"])
    password: str = Field(min_length=8, max_length=128, examples=["strongpass123"])
    full_name: str = Field(min_length=2, max_length=255, examples=["Jane Doe"])
    document: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
        examples=["30123456"],
        description="DNI/documento. Obligatorio para clientes.",
    )
    kind_role: GymAssignableRole | None = Field(
        default=None,
        examples=["client"],
        description="Rol a asignar. Solo respetado si el caller es OWNER.",
    )


class UserCreatedResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    document: str | None = None
    role: str
    gym_id: uuid.UUID
    is_active: bool = True
    biometric_consent_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GymClientResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    document: str | None = None
    role: str
    gym_id: uuid.UUID
    is_active: bool
    biometric_consent_at: datetime | None = None
    active_membership: ActiveMembershipSummary | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GymUserUpdate(BaseModel):
    document: str | None = Field(default=None, min_length=3, max_length=50)
    grant_biometric_consent: bool | None = Field(
        default=None,
        description="True otorga consentimiento biométrico; False lo revoca.",
    )
