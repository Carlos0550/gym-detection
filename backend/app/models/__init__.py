"""Modelos SQLAlchemy del proyecto.

Importar los modelos aquí para que ``Base.metadata`` los vea y Alembic
pueda autogenerar migraciones.
"""

from app.models.access_log import AccessLog
from app.models.base import Base
from app.models.face_embedding import FaceEmbedding
from app.models.gym import Gym
from app.models.gym_user import GymUser
from app.models.membership import Membership
from app.models.user import User

__all__ = [
    "AccessLog",
    "Base",
    "FaceEmbedding",
    "Gym",
    "GymUser",
    "Membership",
    "User",
]
