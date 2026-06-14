"""Enums compartidos por los modelos y la lógica de negocio."""

import enum
from datetime import date


class GymUserRole(str, enum.Enum):
    """Rol de un user DENTRO de un gym específico.

    Los roles se evalúan de menor a mayor privilegio:
        client < manager < owner
    """

    CLIENT = "client"
    MANAGER = "manager"
    OWNER = "owner"


# Jerarquía explícita para chequeos de "rol mínimo requerido".
ROLE_HIERARCHY: dict[GymUserRole, int] = {
    GymUserRole.CLIENT: 1,
    GymUserRole.MANAGER: 2,
    GymUserRole.OWNER: 3,
}


def has_at_least(role: GymUserRole, minimum: GymUserRole) -> bool:
    """True si `role` tiene al menos los privilegios de `minimum`."""
    return ROLE_HIERARCHY[role] >= ROLE_HIERARCHY[minimum]


class MembershipStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


class AccessResult(str, enum.Enum):
    GRANTED = "granted"
    DENIED = "denied"
    UNKNOWN = "unknown"
    LOW_CONFIDENCE = "low_confidence"


def is_membership_active(
    status: MembershipStatus,
    start_date: date,
    end_date: date | None,
    *,
    on_date: date | None = None,
) -> bool:
    """True si la membresía está vigente en la fecha indicada."""
    today = on_date or date.today()
    if status != MembershipStatus.ACTIVE:
        return False
    if start_date > today:
        return False
    if end_date is not None and end_date < today:
        return False
    return True
