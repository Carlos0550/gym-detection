"""Seed inicial: crea superadmin + gym de demo + asigna rol owner.

Uso:
    docker compose exec backend python -m app.seed

Implementación completa en Etapa 1 cuando existan los modelos.
Por ahora es un stub que verifica conectividad a la DB.
"""

import asyncio

import structlog
from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.core.config import get_settings

logger = structlog.get_logger()


async def _check_db() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        result.scalar_one()
        logger.info("seed.db_connection_ok")


async def main() -> None:
    settings = get_settings()
    logger.info(
        "seed.start",
        superadmin_email=settings.seed_superadmin_email,
        gym_name=settings.seed_gym_name,
    )
    await _check_db()
    logger.warning(
        "seed.not_implemented",
        message="Seed completo se implementa en Etapa 1 cuando existan los modelos.",
    )


if __name__ == "__main__":
    asyncio.run(main())
