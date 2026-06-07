"""DTOs del módulo gyms."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GymBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    address: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=50)
    is_active: bool = True


class GymCreate(GymBase):
    pass


class GymUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    address: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None


class GymResponse(GymBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
