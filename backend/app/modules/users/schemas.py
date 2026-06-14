"""DTOs del módulo users."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


GymAssignableRole = Literal["client", "manager"]


class ActiveMembershipSummary(BaseModel):
    id: uuid.UUID
    status: str
    start_date: date
    end_date: date | None = None


class UserCreateByGymMember(BaseModel):
    email: EmailStr | None = Field(
        default=None,
        examples=["newmember@gym.com"],
        description="Opcional si se envía DNI/documento.",
    )
    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
        examples=["strongpass123"],
        description="Opcional; se genera una contraseña segura si no se envía.",
    )
    full_name: str = Field(min_length=2, max_length=255, examples=["Jane Doe"])
    document: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
        examples=["30123456"],
        description="DNI/documento. Opcional si se envía email.",
    )
    kind_role: GymAssignableRole | None = Field(
        default=None,
        examples=["client"],
        description="Rol a asignar. Solo respetado si el caller es OWNER.",
    )

    @model_validator(mode="after")
    def require_email_or_document(self) -> "UserCreateByGymMember":
        has_email = self.email is not None and str(self.email).strip()
        has_document = self.document is not None and self.document.strip()
        if not has_email and not has_document:
            raise ValueError("Ingresá email o DNI para identificar al miembro")
        return self


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
    temporary_password: str | None = Field(
        default=None,
        description="Contraseña generada automáticamente; solo presente si no se envió password.",
    )

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
