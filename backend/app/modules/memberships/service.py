"""Lógica de membresías."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError
from app.models.enums import GymUserRole, MembershipStatus
from app.models.membership import Membership
from app.modules.users.service import get_gym_user_link


async def create_membership(
    db: AsyncSession,
    *,
    gym_id: uuid.UUID,
    user_id: uuid.UUID,
    start_date: date,
    end_date: date | None = None,
) -> Membership:
    _user, link = await get_gym_user_link(db, gym_id, user_id)

    if link.role != GymUserRole.CLIENT:
        raise ForbiddenError("Solo clientes pueden tener membresías")

    if end_date is not None and end_date < start_date:
        raise ConflictError("La fecha de fin no puede ser anterior al inicio")

    membership = Membership(
        gym_user_id=link.id,
        gym_id=gym_id,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        status=MembershipStatus.ACTIVE,
    )
    db.add(membership)
    await db.commit()
    await db.refresh(membership)
    return membership
