"""Modelos SQLAlchemy del proyecto.

En Etapa 0 este módulo sólo reexporta ``Base`` para que Alembic tenga un
target_metadata válido. Los modelos concretos (User, Gym, Member, etc.) se
agregan en Etapas 1–5.
"""

from app.models.base import Base

__all__ = ["Base"]
