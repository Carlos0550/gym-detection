"""DTOs Pydantic del módulo auth."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegisterRequest(BaseModel):
    """Body para POST /auth/register. Solo accesible por superadmin."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=255)
    is_superadmin: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos


class GymMembershipOut(BaseModel):
    gym_id: uuid.UUID
    gym_name: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class MeResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    is_superadmin: bool
    is_active: bool
    created_at: datetime
    memberships: list[GymMembershipOut]

    model_config = ConfigDict(from_attributes=True)
