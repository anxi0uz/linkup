import pytest
from httpx import AsyncClient

from tests.support import RegisterUser

pytestmark = pytest.mark.anyio


async def test_company_crud_and_slug_conflicts(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    owner = await register_user("owner@example.com")

    create_response = await client.post(
        "/api/v1/companies",
        headers=owner.headers,
        json={
            "name": "  LinkUp Labs  ",
            "slug": "  LINKUP-LABS  ",
            "description": "Initial description",
            "location": "Helsinki",
        },
    )

    assert create_response.status_code == 201

    company = create_response.json()
    company_id = company["id"]

    assert company["owner_id"] == owner.id
    assert company["name"] == "LinkUp Labs"
    assert company["slug"] == "linkup-labs"

    duplicate_response = await client.post(
        "/api/v1/companies",
        headers=owner.headers,
        json={
            "name": "Duplicate",
            "slug": "linkup-labs",
        },
    )
    list_response = await client.get(
        "/api/v1/companies",
        headers=owner.headers,
    )
    get_response = await client.get(
        f"/api/v1/companies/{company_id}",
        headers=owner.headers,
    )
    update_response = await client.patch(
        f"/api/v1/companies/{company_id}",
        headers=owner.headers,
        json={
            "name": "LinkUp Engineering",
            "description": None,
        },
    )

    assert duplicate_response.status_code == 409
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [company_id]
    assert get_response.status_code == 200
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "LinkUp Engineering"
    assert update_response.json()["description"] is None

    delete_response = await client.delete(
        f"/api/v1/companies/{company_id}",
        headers=owner.headers,
    )
    deleted_get_response = await client.get(
        f"/api/v1/companies/{company_id}",
        headers=owner.headers,
    )

    assert delete_response.status_code == 204
    assert deleted_get_response.status_code == 404


async def test_only_owner_can_change_company(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    owner = await register_user("company-owner@example.com")
    other_user = await register_user("company-other@example.com")

    create_response = await client.post(
        "/api/v1/companies",
        headers=owner.headers,
        json={
            "name": "Private Control",
            "slug": "private-control",
        },
    )
    company_id = create_response.json()["id"]

    read_response = await client.get(
        f"/api/v1/companies/{company_id}",
        headers=other_user.headers,
    )
    update_response = await client.patch(
        f"/api/v1/companies/{company_id}",
        headers=other_user.headers,
        json={"name": "Hijacked"},
    )
    delete_response = await client.delete(
        f"/api/v1/companies/{company_id}",
        headers=other_user.headers,
    )
    unauthenticated_response = await client.get(
        f"/api/v1/companies/{company_id}",
    )

    assert read_response.status_code == 200
    assert update_response.status_code == 403
    assert delete_response.status_code == 403
    assert unauthenticated_response.status_code == 401


async def test_company_update_rejects_existing_slug(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    owner = await register_user("slug-owner@example.com")

    first_response = await client.post(
        "/api/v1/companies",
        headers=owner.headers,
        json={"name": "First", "slug": "first"},
    )
    second_response = await client.post(
        "/api/v1/companies",
        headers=owner.headers,
        json={"name": "Second", "slug": "second"},
    )

    conflict_response = await client.patch(
        f"/api/v1/companies/{second_response.json()['id']}",
        headers=owner.headers,
        json={"slug": first_response.json()["slug"]},
    )
    invalid_slug_response = await client.post(
        "/api/v1/companies",
        headers=owner.headers,
        json={"name": "Invalid", "slug": "not a slug"},
    )

    assert conflict_response.status_code == 409
    assert invalid_slug_response.status_code == 422
