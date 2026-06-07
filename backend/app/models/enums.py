"""Enums compartidos por los modelos y la lógica de negocio."""

import enum


class GymUserRole(str, enum.Enum):
    """Rol de un user DENTRO de un gym específico.

    Los roles se evalúan de menor a mayor privilegio:
        operator < manager < owner
    """

    OPERATOR = "operator"
    MANAGER = "manager"
    OWNER = "owner"


# Jerarquía explícita para chequeos de "rol mínimo requerido".
ROLE_HIERARCHY: dict[GymUserRole, int] = {
    GymUserRole.OPERATOR: 1,
    GymUserRole.MANAGER: 2,
    GymUserRole.OWNER: 3,
}


def has_at_least(role: GymUserRole, minimum: GymUserRole) -> bool:
    """True si `role` tiene al menos los privilegios de `minimum`."""
    return ROLE_HIERARCHY[role] >= ROLE_HIERARCHY[minimum]
