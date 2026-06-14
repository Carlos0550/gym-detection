"""Tests de membresías."""

from datetime import date

import pytest
from httpx import AsyncClient

from app.models.gym import Gym
from app.models.user import User
from tests.conftest import auth_headers

pytestmark = pytest.mark.asyncio


async def test_create_membership(
    client: AsyncClient,
    owner_token: str,
    owner_link,
    gym: Gym,
    client_user: User,
    client_link,
):
    response = await client.post(
        f"/api/v1/gyms/{gym.id}/users/{client_user.id}/memberships",
        json={"start_date": "2026-01-01", "end_date": "2026-12-31"},
        headers=auth_headers(owner_token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "active"
    assert data["user_id"] == str(client_user.id)
