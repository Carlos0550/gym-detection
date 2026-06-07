"""Tests del módulo gyms."""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers


pytestmark = pytest.mark.asyncio


async def test_list_gyms_as_superadmin_returns_all(
    client: AsyncClient, superadmin_token: str, gym
):
    response = await client.get(
        "/api/v1/gyms", headers=auth_headers(superadmin_token)
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(g["name"] == "Test Gym" for g in data)


async def test_list_gyms_as_member_returns_only_their_gyms(
    client: AsyncClient, owner_token: str, owner_link, gym
):
    response = await client.get(
        "/api/v1/gyms", headers=auth_headers(owner_token)
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Gym"


async def test_list_gyms_as_user_without_membership_returns_empty(
    client: AsyncClient, client_token: str
):
    response = await client.get(
        "/api/v1/gyms", headers=auth_headers(client_token)
    )
    assert response.status_code == 200
    assert response.json() == []


async def test_list_gyms_without_token_returns_401(client: AsyncClient):
    response = await client.get("/api/v1/gyms")
    assert response.status_code == 401


async def test_create_gym_requires_superadmin(
    client: AsyncClient, client_token: str
):
    response = await client.post(
        "/api/v1/gyms",
        json={"name": "New Gym", "address": "x", "phone": "y"},
        headers=auth_headers(client_token),
    )
    assert response.status_code == 403


async def test_create_gym_as_superadmin(
    client: AsyncClient, superadmin_token: str
):
    response = await client.post(
        "/api/v1/gyms",
        json={
            "name": "Brand New",
            "address": "Av Siempre Viva 742",
            "phone": "+541144444444",
        },
        headers=auth_headers(superadmin_token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Brand New"
    assert data["is_active"] is True


async def test_get_gym_as_member(
    client: AsyncClient, client_token: str, client_link, gym
):
    response = await client.get(
        f"/api/v1/gyms/{gym.id}", headers=auth_headers(client_token)
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test Gym"


async def test_get_gym_as_non_member_returns_403(
    client: AsyncClient, client_token: str, gym
):
    # client_token no está vinculado al gym
    response = await client.get(
        f"/api/v1/gyms/{gym.id}", headers=auth_headers(client_token)
    )
    assert response.status_code == 403


async def test_get_gym_not_found(client: AsyncClient, superadmin_token: str):
    import uuid

    response = await client.get(
        f"/api/v1/gyms/{uuid.uuid4()}",
        headers=auth_headers(superadmin_token),
    )
    assert response.status_code == 404


async def test_update_gym_requires_owner(
    client: AsyncClient, client_token: str, client_link, gym
):
    response = await client.patch(
        f"/api/v1/gyms/{gym.id}",
        json={"name": "Hacked"},
        headers=auth_headers(client_token),
    )
    assert response.status_code == 403


async def test_update_gym_as_owner(
    client: AsyncClient, owner_token: str, owner_link, gym
):
    response = await client.patch(
        f"/api/v1/gyms/{gym.id}",
        json={"name": "Renamed Gym", "is_active": False},
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Renamed Gym"
    assert data["is_active"] is False


async def test_update_gym_as_superadmin_anywhere(
    client: AsyncClient, superadmin_token: str, gym
):
    response = await client.patch(
        f"/api/v1/gyms/{gym.id}",
        json={"address": "New address"},
        headers=auth_headers(superadmin_token),
    )
    assert response.status_code == 200
    assert response.json()["address"] == "New address"
