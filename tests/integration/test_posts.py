import pytest
from httpx import AsyncClient

from tests.support import RegisterUser

pytestmark = pytest.mark.anyio


async def test_personal_post_crud_and_validation(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    author = await register_user("post-author@example.com")

    create_response = await client.post(
        "/api/v1/posts",
        headers=author.headers,
        json={"content": "  First post  "},
    )

    assert create_response.status_code == 201

    post = create_response.json()
    post_id = post["id"]

    assert post["author_id"] == author.id
    assert post["company_id"] is None
    assert post["content"] == "First post"

    get_response = await client.get(
        f"/api/v1/posts/{post_id}",
        headers=author.headers,
    )
    list_response = await client.get(
        "/api/v1/posts",
        headers=author.headers,
        params={"author_id": author.id},
    )
    update_response = await client.patch(
        f"/api/v1/posts/{post_id}",
        headers=author.headers,
        json={"content": "  Updated post  "},
    )
    empty_content_response = await client.patch(
        f"/api/v1/posts/{post_id}",
        headers=author.headers,
        json={"content": "   "},
    )
    null_content_response = await client.patch(
        f"/api/v1/posts/{post_id}",
        headers=author.headers,
        json={"content": None},
    )

    assert get_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [post_id]
    assert update_response.status_code == 200
    assert update_response.json()["content"] == "Updated post"
    assert empty_content_response.status_code == 422
    assert null_content_response.status_code == 422

    delete_response = await client.delete(
        f"/api/v1/posts/{post_id}",
        headers=author.headers,
    )
    deleted_get_response = await client.get(
        f"/api/v1/posts/{post_id}",
        headers=author.headers,
    )

    assert delete_response.status_code == 204
    assert deleted_get_response.status_code == 404


async def test_company_posts_require_company_owner(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    owner = await register_user("post-company-owner@example.com")
    other_user = await register_user("post-company-other@example.com")

    company_response = await client.post(
        "/api/v1/companies",
        headers=owner.headers,
        json={
            "name": "Post Company",
            "slug": "post-company",
        },
    )
    company_id = company_response.json()["id"]

    create_response = await client.post(
        "/api/v1/posts",
        headers=owner.headers,
        json={
            "content": "Company announcement",
            "company_id": company_id,
        },
    )

    assert create_response.status_code == 201

    post_id = create_response.json()["id"]

    forbidden_create_response = await client.post(
        "/api/v1/posts",
        headers=other_user.headers,
        json={
            "content": "Unauthorized announcement",
            "company_id": company_id,
        },
    )
    missing_company_response = await client.post(
        "/api/v1/posts",
        headers=owner.headers,
        json={
            "content": "Missing company",
            "company_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    company_posts_response = await client.get(
        "/api/v1/posts",
        headers=other_user.headers,
        params={"company_id": company_id},
    )
    forbidden_update_response = await client.patch(
        f"/api/v1/posts/{post_id}",
        headers=other_user.headers,
        json={"content": "Hijacked"},
    )
    forbidden_delete_response = await client.delete(
        f"/api/v1/posts/{post_id}",
        headers=other_user.headers,
    )

    assert forbidden_create_response.status_code == 403
    assert missing_company_response.status_code == 404
    assert [item["id"] for item in company_posts_response.json()] == [post_id]
    assert forbidden_update_response.status_code == 403
    assert forbidden_delete_response.status_code == 403

    company_delete_response = await client.delete(
        f"/api/v1/companies/{company_id}",
        headers=owner.headers,
    )
    cascaded_post_response = await client.get(
        f"/api/v1/posts/{post_id}",
        headers=owner.headers,
    )

    assert company_delete_response.status_code == 204
    assert cascaded_post_response.status_code == 404


async def test_post_list_filters_and_authentication(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    first_user = await register_user("first-post-list@example.com")
    second_user = await register_user("second-post-list@example.com")

    first_post_response = await client.post(
        "/api/v1/posts",
        headers=first_user.headers,
        json={"content": "First user's post"},
    )
    second_post_response = await client.post(
        "/api/v1/posts",
        headers=second_user.headers,
        json={"content": "Second user's post"},
    )

    filtered_response = await client.get(
        "/api/v1/posts",
        headers=first_user.headers,
        params={"author_id": first_user.id},
    )
    limited_response = await client.get(
        "/api/v1/posts",
        headers=first_user.headers,
        params={"limit": 1},
    )
    unauthenticated_response = await client.get(
        "/api/v1/posts",
    )

    assert first_post_response.status_code == 201
    assert second_post_response.status_code == 201
    assert [item["id"] for item in filtered_response.json()] == [
        first_post_response.json()["id"]
    ]
    assert len(limited_response.json()) == 1
    assert unauthenticated_response.status_code == 401
