import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_user_can_update_and_read_profile(
    client: AsyncClient,
) -> None:
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "test-password",
            "first_name": "test",
            "last_name": "test",
        },
    )
    assert register_response.status_code == 201

    registration = register_response.json()
    access_token = registration["access_token"]
    user_id = registration["user"]["id"]

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    update_response = await client.patch(
        "/api/v1/profile/me",
        headers=headers,
        json={
            "first_name": "Updated",
            "headline": "tester",
            "location": "Helsinki",
        },
    )
    assert update_response.status_code == 200

    updated_profile = update_response.json()

    assert updated_profile["user_id"] == user_id
    assert updated_profile["first_name"] == "Updated"
    assert updated_profile["last_name"] == "test"
    assert updated_profile["headline"] == "tester"
    assert updated_profile["location"] == "Helsinki"

    get_response = await client.get(
        f"/api/v1/profile/{user_id}",
        headers=headers,
    )

    assert get_response.status_code == 200

    stored_profile = get_response.json()

    assert stored_profile["first_name"] == "Updated"
    assert stored_profile["headline"] == "tester"
    assert stored_profile["location"] == "Helsinki"
