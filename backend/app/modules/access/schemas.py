"""DTOs de verificación y access logs."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MembershipBrief(BaseModel):
    id: uuid.UUID
    status: str
    start_date: str
    end_date: str | None = None


class UserBrief(BaseModel):
    id: uuid.UUID
    full_name: str
    document: str | None = None
    email: str


class VerifyFaceResponse(BaseModel):
    matched: bool
    confidence: float | None = None
    result: str
    access: str
    user: UserBrief | None = None
    membership: MembershipBrief | None = None
    reason: str | None = None
    log_id: uuid.UUID


class AccessLogResponse(BaseModel):
    id: uuid.UUID
    gym_id: uuid.UUID
    user_id: uuid.UUID | None = None
    user_full_name: str | None = None
    user_document: str | None = None
    result: str
    confidence: float | None = None
    membership_status: str | None = None
    detail: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccessLogListResponse(BaseModel):
    items: list[AccessLogResponse]
    limit: int
    offset: int
