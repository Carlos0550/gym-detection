"""Tests del módulo auth (login, me). El alta de usuarios vive en test_users.py."""

import pytest
from httpx import AsyncClient

from app.models.user import User
from tests.conftest import auth_headers


pytestmark = pytest.mark.asyncio


async def test_login_with_valid_credentials_returns_token(
    client: AsyncClient, superadmin_user: User
):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": superadmin_user.email, "password": "superpass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


async def test_login_with_invalid_credentials_returns_401(
    client: AsyncClient, superadmin_user: User
):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": superadmin_user.email, "password": "wrong-password"},
    )
    assert response.status_code == 401


async def test_login_with_unknown_email_returns_401(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "doesntmatter"},
    )
    assert response.status_code == 401


async def test_login_with_inactive_user_returns_401(
    client: AsyncClient, superadmin_user: User, engine
):
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        result = await session.execute(
            select(User).where(User.email == superadmin_user.email)
        )
        user = result.scalar_one()
        user.is_active = False
        await session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": superadmin_user.email, "password": "superpass123"},
    )
    assert response.status_code == 401


async def test_me_without_memberships(
    client: AsyncClient, superadmin_token: str, superadmin_user: User
):
    response = await client.get(
        "/api/v1/auth/me", headers=auth_headers(superadmin_token)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == superadmin_user.email
    assert data["is_superadmin"] is True
    assert data["memberships"] == []


async def test_me_returns_memberships(
    client: AsyncClient, owner_user: User, owner_token: str, owner_link, gym
):
    response = await client.get(
        "/api/v1/auth/me", headers=auth_headers(owner_token)
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["memberships"]) == 1
    assert data["memberships"][0]["gym_id"] == str(gym.id)
    assert data["memberships"][0]["gym_name"] == gym.name
    assert data["memberships"][0]["role"] == "owner"


async def test_me_without_token_returns_401(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_me_with_invalid_token_returns_401(client: AsyncClient):
    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401
