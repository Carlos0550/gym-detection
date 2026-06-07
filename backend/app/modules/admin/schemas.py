"""DTOs del módulo admin (endpoints restringidos a superadmin)."""

from pydantic import BaseModel, EmailStr, Field


class AdminCreateUserRequest(BaseModel):
    """Body para POST /admin/users. Solo accesible por superadmin.

    Diferencias con /auth/register:
        - Permite setear is_superadmin y is_active.
        - Devuelve 403 si el caller no es superadmin.
    """

    email: EmailStr = Field(examples=["admin@gym.com"])
    password: str = Field(min_length=8, max_length=128, examples=["adminpass789"])
    full_name: str = Field(min_length=2, max_length=255, examples=["Admin User"])
    is_superadmin: bool = False
    is_active: bool = True
