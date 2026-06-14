"""Tests de enrolamiento facial."""

import pytest
from httpx import AsyncClient

from app.models.gym import Gym
from app.models.user import User
from tests.conftest import auth_headers, enroll_frames, fake_jpeg

pytestmark = pytest.mark.asyncio


async def test_enroll_requires_consent(
    client_with_face: AsyncClient,
    owner_token: str,
    owner_link,
    gym: Gym,
    client_user: User,
    client_link,
):
    response = await client_with_face.post(
        f"/api/v1/gyms/{gym.id}/users/{client_user.id}/face/enroll",
        headers=auth_headers(owner_token),
        files=enroll_frames(),
    )
    assert response.status_code == 403
    assert "Consentimiento" in response.json()["detail"]


async def test_enroll_success(
    client_with_face: AsyncClient,
    owner_token: str,
    owner_link,
    gym: Gym,
    client_user: User,
    consented_client_link,
):
    response = await client_with_face.post(
        f"/api/v1/gyms/{gym.id}/users/{client_user.id}/face/enroll",
        headers=auth_headers(owner_token),
        files=enroll_frames(),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["gym_id"] == str(gym.id)
    assert data["user_id"] == str(client_user.id)


async def test_enroll_duplicate_face(
    client_with_face: AsyncClient,
    owner_token: str,
    owner_link,
    gym: Gym,
    client_user: User,
    consented_client_link,
    engine,
):
    files = enroll_frames("same.jpg")
    await client_with_face.post(
        f"/api/v1/gyms/{gym.id}/users/{client_user.id}/face/enroll",
        headers=auth_headers(owner_token),
        files=files,
    )

    create = await client_with_face.post(
        f"/api/v1/gyms/{gym.id}/users",
        json={
            "email": "other@example.com",
            "password": "newpass1234",
            "full_name": "Other Client",
            "document": "30999888",
        },
        headers=auth_headers(owner_token),
    )
    other_id = create.json()["id"]

    await client_with_face.patch(
        f"/api/v1/gyms/{gym.id}/users/{other_id}",
        json={"grant_biometric_consent": True},
        headers=auth_headers(owner_token),
    )

    dup = await client_with_face.post(
        f"/api/v1/gyms/{gym.id}/users/{other_id}/face/enroll",
        headers=auth_headers(owner_token),
        files=enroll_frames("same.jpg"),
    )
    assert dup.status_code == 409
