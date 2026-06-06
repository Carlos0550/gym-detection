"""Base declarativa para todos los modelos SQLAlchemy del proyecto.

Reexportada desde ``app.core.database`` para que Alembic pueda importar
``Base.metadata`` sin generar import circular.
"""

from app.core.database import Base

__all__ = ["Base"]
