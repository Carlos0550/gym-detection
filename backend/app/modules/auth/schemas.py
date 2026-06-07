"""DTOs Pydantic del módulo auth."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr = Field(examples=["john@doe.com"])
    password: str = Field(min_length=8, max_length=128, examples=["strongpass123"])


class TokenResponse(BaseModel):
    access_token: str = Field(examples=["eyJhbGciOiJIUzI1NiIs..."])
    token_type: str = "bearer"
    expires_in: int = Field(examples=[3600])


class GymMembershipOut(BaseModel):
    gym_id: uuid.UUID = Field(examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"])
    gym_name: str = Field(examples=["Fit Center Palermo"])
    role: str = Field(examples=["owner"])

    model_config = ConfigDict(from_attributes=True)


class MeResponse(BaseModel):
    id: uuid.UUID = Field(examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"])
    email: EmailStr = Field(examples=["john@doe.com"])
    full_name: str = Field(examples=["John Doe"])
    is_superadmin: bool = False
    is_active: bool = True
    created_at: datetime = Field(examples=["2026-06-07T03:00:00Z"])
    memberships: list[GymMembershipOut]

    model_config = ConfigDict(from_attributes=True)
