"""DTOs de membresías."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class MembershipCreate(BaseModel):
    start_date: date = Field(examples=["2026-01-01"])
    end_date: date | None = Field(default=None, examples=["2026-12-31"])


class MembershipResponse(BaseModel):
    id: uuid.UUID
    gym_user_id: uuid.UUID
    gym_id: uuid.UUID
    user_id: uuid.UUID
    start_date: date
    end_date: date | None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
