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
            "document": "30111111",
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
            "document": "30222222",
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
            "document": "30333333",
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
            "document": "30444444",
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


async def test_create_gym_user_duplicate_email_same_gym_returns_409(
    client: AsyncClient,
    owner_token: str,
    owner_link,
    gym: Gym,
    client_user: User,
    client_link,
):
    response = await client.post(
        f"/api/v1/gyms/{gym.id}/users",
        json={
            "email": client_user.email,
            "password": "newpass1234",
            "full_name": "Dup",
            "document": "30555555",
        },
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 409
    assert "este gimnasio" in response.json()["detail"].lower()


async def test_same_email_allowed_in_different_gym_links_existing_user(
    client: AsyncClient,
    owner_token: str,
    owner_link,
    gym: Gym,
    client_user: User,
    engine,
    owner_user: User,
):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.models.enums import GymUserRole
    from app.models.gym import Gym as GymModel
    from app.models.gym_user import GymUser

    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        other_gym = GymModel(name="Other Gym Email", address="X", phone="+5491100000003")
        session.add(other_gym)
        await session.flush()
        session.add(
            GymUser(gym_id=other_gym.id, user_id=owner_user.id, role=GymUserRole.OWNER)
        )
        await session.commit()
        other_id = other_gym.id

    response = await client.post(
        f"/api/v1/gyms/{other_id}/users",
        json={
            "email": client_user.email,
            "full_name": "Same Email Other Gym",
            "document": "30555556",
        },
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == str(client_user.id)
    assert data["email"] == client_user.email
    assert data["gym_id"] == str(other_id)
    assert data["temporary_password"] is None


async def test_create_gym_user_normalizes_email(
    client: AsyncClient, owner_token: str, owner_link, gym: Gym
):
    response = await client.post(
        f"/api/v1/gyms/{gym.id}/users",
        json={
            "email": "MiXeD@Example.COM",
            "password": "newpass1234",
            "full_name": "Mixed",
            "document": "30666666",
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
            "document": "30777777",
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


async def test_create_without_email_or_document_returns_422(
    client: AsyncClient, owner_token: str, owner_link, gym: Gym
):
    response = await client.post(
        f"/api/v1/gyms/{gym.id}/users",
        json={
            "full_name": "Sin identificador",
        },
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 422


async def test_create_with_only_email(
    client: AsyncClient, owner_token: str, owner_link, gym: Gym
):
    response = await client.post(
        f"/api/v1/gyms/{gym.id}/users",
        json={
            "email": "onlyemail@example.com",
            "full_name": "Solo Email",
        },
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "onlyemail@example.com"
    assert data["document"] is None


async def test_create_with_only_document(
    client: AsyncClient, owner_token: str, owner_link, gym: Gym
):
    response = await client.post(
        f"/api/v1/gyms/{gym.id}/users",
        json={
            "full_name": "Solo DNI",
            "document": "30999999",
        },
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["document"] == "30999999"
    assert data["email"].endswith("@gym-detection.internal")


async def test_create_auto_generates_password(
    client: AsyncClient, owner_token: str, owner_link, gym: Gym
):
    response = await client.post(
        f"/api/v1/gyms/{gym.id}/users",
        json={
            "email": "autopass@example.com",
            "full_name": "Auto Pass",
            "document": "30888888",
        },
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["temporary_password"]
    assert len(data["temporary_password"]) >= 8

    login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "autopass@example.com",
            "password": data["temporary_password"],
        },
    )
    assert login.status_code == 200


async def test_duplicate_document_same_gym_returns_409(
    client: AsyncClient, owner_token: str, owner_link, gym: Gym, client_link
):
    response = await client.post(
        f"/api/v1/gyms/{gym.id}/users",
        json={
            "email": "dupdni@example.com",
            "password": "newpass1234",
            "full_name": "Dup DNI",
            "document": "30123456",
        },
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 409


async def test_same_document_allowed_in_different_gym(
    client: AsyncClient,
    owner_token: str,
    owner_link,
    gym: Gym,
    client_link,
    engine,
    owner_user: User,
):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.models.enums import GymUserRole
    from app.models.gym import Gym as GymModel
    from app.models.gym_user import GymUser

    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        other_gym = GymModel(name="Other Gym Doc", address="X", phone="+5491100000002")
        session.add(other_gym)
        await session.flush()
        session.add(
            GymUser(gym_id=other_gym.id, user_id=owner_user.id, role=GymUserRole.OWNER)
        )
        await session.commit()
        other_id = other_gym.id

    response = await client.post(
        f"/api/v1/gyms/{other_id}/users",
        json={
            "email": "same-dni-other-gym@example.com",
            "password": "newpass1234",
            "full_name": "Same DNI Other Gym",
            "document": "30123456",
        },
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 201


async def test_list_gym_clients(
    client: AsyncClient, owner_token: str, owner_link, gym: Gym, client_link, active_membership
):
    response = await client.get(
        f"/api/v1/gyms/{gym.id}/users",
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["document"] == "30123456"
    assert data[0]["active_membership"] is not None
    assert data[0]["active_membership"]["status"] == "active"


async def test_patch_biometric_consent(
    client: AsyncClient, owner_token: str, owner_link, gym: Gym, client_user: User, client_link
):
    response = await client.patch(
        f"/api/v1/gyms/{gym.id}/users/{client_user.id}",
        json={"grant_biometric_consent": True},
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 200
    assert response.json()["biometric_consent_at"] is not None
