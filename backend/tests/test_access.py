"""Tests de verificación facial y access logs."""

import pytest
from httpx import AsyncClient

from app.models.gym import Gym
from app.models.user import User
from tests.conftest import auth_headers, enroll_frames, fake_jpeg

pytestmark = pytest.mark.asyncio


async def _enroll_client(
    client: AsyncClient,
    token: str,
    gym_id,
    user_id,
    image_name: str = "enroll.jpg",
):
    await client.patch(
        f"/api/v1/gyms/{gym_id}/users/{user_id}",
        json={"grant_biometric_consent": True},
        headers=auth_headers(token),
    )
    await client.post(
        f"/api/v1/gyms/{gym_id}/users/{user_id}/face/enroll",
        headers=auth_headers(token),
        files=enroll_frames(image_name),
    )


def _verify_files(match_name: str = "enroll.jpg"):
    return [
        ("frames", fake_jpeg("liveness-a.jpg")),
        ("frames", fake_jpeg(match_name)),
    ]


async def test_verify_grants_access_with_active_membership(
    client_with_face: AsyncClient,
    manager_token: str,
    manager_link,
    owner_token: str,
    owner_link,
    gym: Gym,
    client_user: User,
    active_membership,
):
    await _enroll_client(client_with_face, owner_token, gym.id, client_user.id)

    response = await client_with_face.post(
        f"/api/v1/gyms/{gym.id}/access/verify-face",
        headers=auth_headers(manager_token),
        files=_verify_files("enroll.jpg"),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["access"] == "granted"
    assert data["matched"] is True
    assert data["user"]["document"] == "30123456"


async def test_verify_denies_without_membership(
    client_with_face: AsyncClient,
    manager_token: str,
    manager_link,
    owner_token: str,
    owner_link,
    gym: Gym,
    client_user: User,
    consented_client_link,
):
    await _enroll_client(client_with_face, owner_token, gym.id, client_user.id)

    response = await client_with_face.post(
        f"/api/v1/gyms/{gym.id}/access/verify-face",
        headers=auth_headers(manager_token),
        files=_verify_files("enroll.jpg"),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["access"] == "denied"
    assert "Membresía" in data["reason"]


async def test_verify_requires_liveness_frames(
    client_with_face: AsyncClient,
    manager_token: str,
    manager_link,
    gym: Gym,
):
    response = await client_with_face.post(
        f"/api/v1/gyms/{gym.id}/access/verify-face",
        headers=auth_headers(manager_token),
        files=[("frames", fake_jpeg("only.jpg"))],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["access"] == "denied"
    assert "frames" in data["reason"].lower() or "vivacidad" in data["reason"].lower()


async def test_list_access_logs(
    client_with_face: AsyncClient,
    manager_token: str,
    manager_link,
    owner_token: str,
    owner_link,
    gym: Gym,
    client_user: User,
    active_membership,
):
    await _enroll_client(client_with_face, owner_token, gym.id, client_user.id)
    await client_with_face.post(
        f"/api/v1/gyms/{gym.id}/access/verify-face",
        headers=auth_headers(manager_token),
        files=_verify_files("enroll.jpg"),
    )

    logs = await client_with_face.get(
        f"/api/v1/gyms/{gym.id}/access/logs",
        headers=auth_headers(manager_token),
    )
    assert logs.status_code == 200
    items = logs.json()["items"]
    assert items
    assert items[0]["user_full_name"] == client_user.full_name
    assert items[0]["user_document"] == "30123456"
