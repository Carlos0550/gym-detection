"""Tests del módulo users (POST /gyms/{gym_id}/users)."""

import pytest
from httpx import AsyncClient

from app.models.gym import Gym
from app.models.user import User
from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio


# ============================================================
# Auth
# ============================================================
async def test_create_gym_user_requires_authentication(
    client: AsyncClient, gym: Gym
):
    response = await client.post(
        f"/api/v1/gyms/{gym.id}/users",
        json={
            "email": "x@example.com",
            "password": "newpass1234",
            "full_name": "X",
        },
    )
    assert response.status_code == 401


async def test_create_gym_user_requires_membership(
    client: AsyncClient, owner_token: str, owner_link, gym: Gym, engine
):
    """El owner del gym A no puede crear usuarios en el gym B si no es miembro."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.models.gym import Gym as GymModel

    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        other_gym = GymModel(name="Other Gym", address="Other 123", phone="+5491100000000")
        session.add(other_gym)
        await session.commit()
        await session.refresh(other_gym)

    response = await client.post(
        f"/api/v1/gyms/{other_gym.id}/users",
        json={
            "email": "x@example.com",
            "password": "newpass1234",
            "full_name": "X",
        },
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 403


async def test_create_gym_user_requires_manager_or_owner(
    client: AsyncClient, client_token: str, client_link, gym: Gym
):
    """Un CLIENT del gym no puede crear usuarios (no llega al manager)."""
    response = await client.post(
        f"/api/v1/gyms/{gym.id}/users",
        json={
            "email": "x@example.com",
            "password": "newpass1234",
            "full_name": "X",
        },
        headers=auth_headers(client_token),
    )
    assert response.status_code == 403


# ============================================================
# Owner: kind_role se respeta
# ============================================================
async def test_owner_creates_default_client(
    client: AsyncClient, owner_token: str, owner_link, gym: Gym
):
    response = await client.post(
        f"/api/v1/gyms/{gym.id}/users",
        json={
            "email": "newclient@example.com",
            "password": "newpass1234",
            "full_name": "New Client",
        },
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newclient@example.com"
    assert data["full_name"] == "New Client"
    assert data["role"] == "client"
    assert data["gym_id"] == str(gym.id)
    assert data["is_active"] is True


async def test_owner_creates_explicit_client(
    client: AsyncClient, owner_token: str, owner_link, gym: Gym
):
    response = await client.post(
        f"/api/v1/gyms/{gym.id}/users",
        json={
            "email": "explicitclient@example.com",
            "password": "newpass1234",
            "full_name": "Explicit Client",
            "kind_role": "client",
        },
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 201
    assert response.json()["role"] == "client"


async def test_owner_creates_manager(
    client: AsyncClient, owner_token: str, owner_link, gym: Gym
):
    response = await client.post(
        f"/api/v1/gyms/{gym.id}/users",
        json={
            "email": "newmanager@example.com",
            "password": "newpass1234",
            "full_name": "New Manager",
            "kind_role": "manager",
        },
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 201
    assert response.json()["role"] == "manager"


# ============================================================
# Manager: kind_role se ignora
# ============================================================
async def test_manager_creates_client_without_kind_role(
    client: AsyncClient, manager_token: str, manager_link, gym: Gym
):
    response = await client.post(
        f"/api/v1/gyms/{gym.id}/users",
        json={
            "email": "frommanager@example.com",
            "password": "newpass1234",
            "full_name": "From Manager",
        },
        headers=auth_headers(manager_token),
    )
    assert response.status_code == 201
    assert response.json()["role"] == "client"


async def test_manager_ignores_kind_role_manager(
    client: AsyncClient, manager_token: str, manager_link, gym: Gym
):
    """Aunque el manager mande kind_role=manager, se fuerza CLIENT."""
    response = await client.post(
        f"/api/v1/gyms/{gym.id}/users",
        json={
            "email": "sneakymanager@example.com",
            "password": "newpass1234",
            "full_name": "Sneaky Manager",
            "kind_role": "manager",
        },
        headers=auth_headers(manager_token),
    )
    assert response.status_code == 201
    assert response.json()["role"] == "client"


# ============================================================
# Validación
# ============================================================
async def test_owner_cannot_create_owner_via_kind_role(
    client: AsyncClient, owner_token: str, owner_link, gym: Gym
):
    """``owner`` no es un kind_role válido (Literal client|manager)."""
    response = await client.post(
        f"/api/v1/gyms/{gym.id}/users",
        json={
            "email": "tryowner@example.com",
            "password": "newpass1234",
            "full_name": "Try Owner",
            "kind_role": "owner",
        },
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 422


async def test_create_gym_user_with_duplicate_email_returns_409(
    client: AsyncClient,
    owner_token: str,
    owner_link,
    gym: Gym,
    superadmin_user: User,
):
    response = await client.post(
        f"/api/v1/gyms/{gym.id}/users",
        json={
            "email": superadmin_user.email,
            "password": "newpass1234",
            "full_name": "Dup",
        },
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 409


async def test_create_gym_user_normalizes_email(
    client: AsyncClient, owner_token: str, owner_link, gym: Gym
):
    response = await client.post(
        f"/api/v1/gyms/{gym.id}/users",
        json={
            "email": "MiXeD@Example.COM",
            "password": "newpass1234",
            "full_name": "Mixed",
        },
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 201
    assert response.json()["email"] == "mixed@example.com"


async def test_create_gym_user_with_invalid_email_returns_422(
    client: AsyncClient, owner_token: str, owner_link, gym: Gym
):
    response = await client.post(
        f"/api/v1/gyms/{gym.id}/users",
        json={
            "email": "not-an-email",
            "password": "newpass1234",
            "full_name": "Bad",
        },
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 422


async def test_create_gym_user_with_short_password_returns_422(
    client: AsyncClient, owner_token: str, owner_link, gym: Gym
):
    response = await client.post(
        f"/api/v1/gyms/{gym.id}/users",
        json={
            "email": "short@example.com",
            "password": "short",
            "full_name": "Short",
        },
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 422


# ============================================================
# Verificación de vínculo: el nuevo user puede loguearse y aparece en /me
# ============================================================
async def test_new_user_can_login_and_see_membership(
    client: AsyncClient, owner_token: str, owner_link, gym: Gym
):
    """Crea un user via /gyms/{gym_id}/users y verifica que esté vinculado."""
    create = await client.post(
        f"/api/v1/gyms/{gym.id}/users",
        json={
            "email": "linked@example.com",
            "password": "newpass1234",
            "full_name": "Linked User",
        },
        headers=auth_headers(owner_token),
    )
    assert create.status_code == 201

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "linked@example.com", "password": "newpass1234"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = await client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert me.status_code == 200
    data = me.json()
    assert len(data["memberships"]) == 1
    assert data["memberships"][0]["gym_id"] == str(gym.id)
    assert data["memberships"][0]["role"] == "client"
