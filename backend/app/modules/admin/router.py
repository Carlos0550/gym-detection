"""Endpoints administrativos (solo superadmin).

Acá van operaciones privileged: crear users con flags especiales,
asignar membresías, etc. Si crece, partir en subarchivos
(admin/users.py, admin/gyms.py, ...).
"""

from fastapi import APIRouter, status

from app.core.dependencies import DbSession, Superadmin
from app.modules.admin.schemas import AdminCreateUserRequest
from app.modules.auth.schemas import MeResponse
from app.modules.auth.service import register_user

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/users",
    response_model=MeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    body: AdminCreateUserRequest,
    db: DbSession,
    _: Superadmin,
) -> MeResponse:
    user = await register_user(
        db,
        email=body.email,
        password=body.password,
        full_name=body.full_name,
        is_superadmin=body.is_superadmin,
    )
    if not body.is_active:
        user.is_active = False
        await db.commit()
        await db.refresh(user)
    return MeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_superadmin=user.is_superadmin,
        is_active=user.is_active,
        created_at=user.created_at,
        memberships=[],
    )
