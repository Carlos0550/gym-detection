"""Modelos SQLAlchemy del proyecto.

Etapa 1: User, Gym, GymUser.
Etapas siguientes: Member, Membership, FaceEmbedding, AccessLog, AuditLog.

Importar los modelos aquí (además de en su propio módulo) es la forma
estándar de que ``Base.metadata`` los vea y Alembic pueda autogenerar
migraciones con solo hacer ``from app.models import Base``.
"""

from app.models.base import Base
from app.models.gym import Gym
from app.models.gym_user import GymUser
from app.models.user import User

__all__ = ["Base", "Gym", "GymUser", "User"]
