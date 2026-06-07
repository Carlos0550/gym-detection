"""Tests del módulo admin (endpoints solo para superadmin)."""

import pytest
from httpx import AsyncClient

from app.models.user import User
from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio


# ============================================================
# POST /admin/users
# ============================================================
async def test_admin_create_user_requires_authentication(client: AsyncClient):
    response = await client.post(
        "/api/v1/admin/users",
        json={
            "email": "new@example.com",
            "password": "newpass1234",
            "full_name": "New User",
        },
    )
    assert response.status_code == 401


async def test_admin_create_user_requires_superadmin(
    client: AsyncClient, owner_token: str
):
    response = await client.post(
        "/api/v1/admin/users",
        json={
            "email": "new@example.com",
            "password": "newpass1234",
            "full_name": "New User",
        },
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 403


async def test_admin_create_user_as_superadmin_creates_user(
    client: AsyncClient, superadmin_token: str
):
    response = await client.post(
        "/api/v1/admin/users",
        json={
            "email": "new@example.com",
            "password": "newpass1234",
            "full_name": "New User",
        },
        headers=auth_headers(superadmin_token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@example.com"
    assert data["is_superadmin"] is False
    assert data["is_active"] is True


async def test_admin_create_user_can_create_superadmin(
    client: AsyncClient, superadmin_token: str
):
    """El endpoint admin permite escalar a is_superadmin (es su razón de ser)."""
    response = await client.post(
        "/api/v1/admin/users",
        json={
            "email": "another-super@example.com",
            "password": "newpass1234",
            "full_name": "Another Super",
            "is_superadmin": True,
        },
        headers=auth_headers(superadmin_token),
    )
    assert response.status_code == 201
    assert response.json()["is_superadmin"] is True


async def test_admin_create_user_can_create_inactive_user(
    client: AsyncClient, superadmin_token: str
):
    response = await client.post(
        "/api/v1/admin/users",
        json={
            "email": "inactive@example.com",
            "password": "newpass1234",
            "full_name": "Inactive",
            "is_active": False,
        },
        headers=auth_headers(superadmin_token),
    )
    assert response.status_code == 201
    assert response.json()["is_active"] is False


async def test_admin_create_user_with_duplicate_email_returns_409(
    client: AsyncClient, superadmin_token: str, superadmin_user: User
):
    response = await client.post(
        "/api/v1/admin/users",
        json={
            "email": superadmin_user.email,
            "password": "newpass1234",
            "full_name": "Dup",
        },
        headers=auth_headers(superadmin_token),
    )
    assert response.status_code == 409
