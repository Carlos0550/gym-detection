"""Fixtures compartidos por los tests del backend.

Estrategia:
    - DB: gym_test (creada por ``make test-setup``).
    - Engine: async, session-scoped.
    - Cliente: TestClient sync de FastAPI (no toca el laberinto asyncio).
    - App usa su propio engine (sobreescribimos DATABASE_URL en este
      conftest antes de importar la app, así el engine interno apunta
      a gym_test).
"""

import os

os.environ["DATABASE_URL"] = "postgresql+asyncpg://gym:gym@postgres:5432/gym_test"
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-prod")

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.base import Base
from app.models.enums import GymUserRole
from app.models.gym import Gym
from app.models.gym_user import GymUser
from app.models.user import User

TEST_DB_URL = "postgresql+asyncpg://gym:gym@postgres:5432/gym_test"


# ============================================================
# Engine de tests (session-scoped: shared con el event loop de sesión)
# ============================================================
@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def engine():
    e = create_async_engine(TEST_DB_URL)
    yield e
    await e.dispose()


# ============================================================
# TRUNCATE antes de cada test
# ============================================================
@pytest_asyncio.fixture(autouse=True)
async def _truncate(engine):
    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname='public' AND tablename != 'alembic_version'"
            )
        )
        tables = [row[0] for row in result]
        if tables:
            await conn.execute(
                text(
                    f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE"
                )
            )
    yield


# ============================================================
# Cliente
# ============================================================
@pytest_asyncio.fixture
async def client(engine) -> AsyncGenerator[TestClient, None]:
    """AsyncClient contra la app. La app usa el engine que ya apunta
    a gym_test (gracias al os.environ al inicio de este conftest)."""
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ============================================================
# Factories (async, con session_factory + engine)
# ============================================================
@pytest_asyncio.fixture
async def superadmin_user(engine) -> User:
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        user = User(
            id=uuid.uuid4(),
            email="super@test.com",
            password_hash=hash_password("superpass123"),
            full_name="Super Admin",
            is_superadmin=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def owner_user(engine) -> User:
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        user = User(
            id=uuid.uuid4(),
            email="owner@test.com",
            password_hash=hash_password("ownerpass123"),
            full_name="Gym Owner",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def client_user(engine) -> User:
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        user = User(
            id=uuid.uuid4(),
            email="client@test.com",
            password_hash=hash_password("clientpass123"),
            full_name="Client User",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def gym(engine) -> Gym:
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        g = Gym(name="Test Gym", address="Test 123", phone="+5400000000")
        session.add(g)
        await session.commit()
        await session.refresh(g)
    return g


@pytest_asyncio.fixture
async def owner_link(engine, gym: Gym, owner_user: User) -> GymUser:
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        link = GymUser(
            gym_id=gym.id, user_id=owner_user.id, role=GymUserRole.OWNER
        )
        session.add(link)
        await session.commit()
    return link


@pytest_asyncio.fixture
async def client_link(engine, gym: Gym, client_user: User) -> GymUser:
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        link = GymUser(
            gym_id=gym.id, user_id=client_user.id, role=GymUserRole.CLIENT
        )
        session.add(link)
        await session.commit()
    return link


@pytest_asyncio.fixture
async def superadmin_token(superadmin_user: User) -> str:
    return create_access_token(superadmin_user.id)


@pytest_asyncio.fixture
async def owner_token(owner_user: User) -> str:
    return create_access_token(owner_user.id)


@pytest_asyncio.fixture
async def client_token(client_user: User) -> str:
    return create_access_token(client_user.id)


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
