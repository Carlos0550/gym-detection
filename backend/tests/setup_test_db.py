"""Setup script para preparar la DB de tests.

Se ejecuta ANTES de pytest (ver ``Makefile`` o el comando manual).
Crea la DB ``gym_test`` desde cero y aplica todas las migraciones.

Idempotente: drop+create siempre, así cada corrida empieza limpia.
"""

import os

# Forzar la URL ANTES de cualquier import de la app, porque env.py
# de Alembic lee el env var directamente (no acepta override externo).
os.environ["DATABASE_URL"] = "postgresql+asyncpg://gym:gym@postgres:5432/gym_test"

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import command
from alembic.config import Config

ADMIN_URL = "postgresql+asyncpg://gym:gym@postgres:5432/postgres"
TEST_DB_NAME = "gym_test"
TEST_DB_URL = f"postgresql+asyncpg://gym:gym@postgres:5432/{TEST_DB_NAME}"


async def _reset_test_db() -> None:
    admin = create_async_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        await conn.execute(
            text(
                f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                f"WHERE datname = '{TEST_DB_NAME}' AND pid <> pg_backend_pid()"
            )
        )
        await conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))
        await conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))
    await admin.dispose()


def _alembic_upgrade_head() -> None:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", TEST_DB_URL)
    command.upgrade(cfg, "head")


def main() -> None:
    print(f"[setup_test_db] Resetting {TEST_DB_NAME} ...")
    asyncio.run(_reset_test_db())
    print("[setup_test_db] Applying migrations ...")
    _alembic_upgrade_head()
    print("[setup_test_db] Done.")


if __name__ == "__main__":
    main()
