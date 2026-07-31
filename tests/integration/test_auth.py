import pytest
from httpx import AsyncClient
from redis.asyncio import Redis

pytestmark = pytest.mark.anyio


async def test_registration_refresh_and_logout_lifecycle(
    client: AsyncClient,
    test_redis: Redis,
) -> None:
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "USER@example.com",
            "password": "test-password",
            "first_name": "Test",
            "last_name": "User",
        },
    )

    assert register_response.status_code == 201

    registration = register_response.json()
    access_token = registration["access_token"]
    first_refresh_token = client.cookies.get("refresh_token")

    assert registration["token_type"] == "bearer"
    assert registration["user"]["email"] == "user@example.com"
    assert first_refresh_token is not None
    assert await test_redis.dbsize() == 1

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["id"] == registration["user"]["id"]

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
    )

    assert refresh_response.status_code == 200
    assert refresh_response.json()["access_token"]

    second_refresh_token = client.cookies.get("refresh_token")

    assert second_refresh_token is not None
    assert second_refresh_token != first_refresh_token
    assert await test_redis.dbsize() == 1

    client.cookies.clear()
    client.cookies.set(
        "refresh_token",
        first_refresh_token,
        domain="test.local",
        path="/api/v1/auth",
    )

    reused_refresh_response = await client.post(
        "/api/v1/auth/refresh",
    )

    assert reused_refresh_response.status_code == 401

    client.cookies.clear()
    client.cookies.set(
        "refresh_token",
        second_refresh_token,
        domain="test.local",
        path="/api/v1/auth",
    )

    logout_response = await client.post(
        "/api/v1/auth/logout",
    )

    assert logout_response.status_code == 204
    assert client.cookies.get("refresh_token") is None
    assert await test_redis.dbsize() == 0


async def test_duplicate_registration_and_invalid_login(
    client: AsyncClient,
) -> None:
    registration_data = {
        "email": "duplicate@example.com",
        "password": "test-password",
        "first_name": "Test",
        "last_name": "User",
    }

    first_response = await client.post(
        "/api/v1/auth/register",
        json=registration_data,
    )
    duplicate_response = await client.post(
        "/api/v1/auth/register",
        json=registration_data,
    )
    invalid_login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": registration_data["email"],
            "password": "wrong-password",
        },
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["detail"] == "Email already registered"
    assert invalid_login_response.status_code == 401


async def test_login_issues_tokens_for_registered_user(
    client: AsyncClient,
) -> None:
    registration_data = {
        "email": "login@example.com",
        "password": "test-password",
        "first_name": "Test",
        "last_name": "User",
    }

    await client.post(
        "/api/v1/auth/register",
        json=registration_data,
    )
    client.cookies.clear()

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": registration_data["email"],
            "password": registration_data["password"],
        },
    )

    assert login_response.status_code == 200
    assert login_response.json()["user"]["email"] == registration_data["email"]
    assert client.cookies.get("refresh_token") is not None
