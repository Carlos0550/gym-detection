"""DTOs del módulo gyms."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class GymBase(BaseModel):
    name: str = Field(min_length=2, max_length=255, examples=["Fit Center Palermo"])
    address: str | None = Field(default=None, max_length=500, examples=["Av. Santa Fe 1234, CABA"])
    phone: str | None = Field(default=None, max_length=50, examples=["+5491151234567"])
    is_active: bool = True


class GymCreate(GymBase):
    pass


class GymUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255, examples=["Fit Center Recoleta"])
    address: str | None = Field(default=None, max_length=500, examples=["Av. Quintana 567, CABA"])
    phone: str | None = Field(default=None, max_length=50, examples=["+5491176543210"])
    is_active: bool | None = None


class GymResponse(GymBase):
    id: uuid.UUID = Field(examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"])
    created_at: datetime = Field(examples=["2026-06-07T03:00:00Z"])
    updated_at: datetime = Field(examples=["2026-06-07T03:00:00Z"])

    model_config = ConfigDict(from_attributes=True)


class GymOnboardingResponse(BaseModel):
    gym_name: str = Field(examples=["Fit Center Palermo"])
    gym_address: str = Field(examples=["Av. Santa Fe 1234, CABA"])
    operator_name: str = Field(examples=["John Doe"])
    operator_email: str = Field(examples=["john@doe.com"])
    operator_access_token: str = Field(examples=["eyJhbGciOiJIUzI1NiIs..."])


class GymOnboardingRequest(BaseModel):
    gym_name: str = Field(min_length=2, max_length=255, examples=["Fit Center Palermo"])
    gym_address: str = Field(max_length=500, examples=["Av. Santa Fe 1234, CABA"])
    gym_phone: str = Field(min_length=6, max_length=20, examples=["+5491151234567"])
    operator_name: str = Field(min_length=2, max_length=255, examples=["John Doe"])
    password: str = Field(min_length=8, max_length=128, examples=["strongpass123"])
    email: EmailStr = Field(examples=["john@doe.com"])
