"""DTOs de enrolamiento facial."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FaceEnrollResponse(BaseModel):
    id: uuid.UUID
    gym_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FaceEmbeddingResponse(BaseModel):
    id: uuid.UUID
    gym_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FaceDeleteResponse(BaseModel):
    deleted: int = Field(description="Cantidad de embeddings eliminados")


class PoseValidationResponse(BaseModel):
    ok: bool = True
