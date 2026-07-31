from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from linkup.api.dependencies import SessionDep
from linkup.modules.auth.dependencies import CurrentUserDep
from linkup.modules.companies.exceptions import (
    CompanyNotFoundError,
    CompanyPermissionDeniedError,
)
from linkup.modules.posts.exceptions import (
    PostNotFoundError,
    PostPermissionDeniedError,
)
from linkup.modules.posts.schemas import (
    PostCreate,
    PostResponse,
    PostUpdate,
)
from linkup.modules.posts.service import (
    create_post,
    delete_post,
    get_post_by_id,
    list_posts,
    update_post,
)

router = APIRouter(
    prefix="/posts",
    tags=["Posts"],
)


@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_post_endpoint(
    payload: PostCreate,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> PostResponse:
    try:
        post = await create_post(
            db,
            current_user.id,
            payload,
        )
    except CompanyNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        ) from error
    except CompanyPermissionDeniedError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the company owner can publish for it",
        ) from error

    return PostResponse.model_validate(post)


@router.get(
    "",
    response_model=list[PostResponse],
)
async def list_posts_endpoint(
    current_user: CurrentUserDep,
    db: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    author_id: UUID | None = None,
    company_id: UUID | None = None,
) -> list[PostResponse]:
    posts = await list_posts(
        db,
        limit,
        offset,
        author_id,
        company_id,
    )

    return [PostResponse.model_validate(post) for post in posts]


@router.get(
    "/{post_id}",
    response_model=PostResponse,
)
async def get_post_endpoint(
    post_id: UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> PostResponse:
    try:
        post = await get_post_by_id(
            db,
            post_id,
        )
    except PostNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        ) from error

    return PostResponse.model_validate(post)


@router.patch(
    "/{post_id}",
    response_model=PostResponse,
)
async def update_post_endpoint(
    post_id: UUID,
    payload: PostUpdate,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> PostResponse:
    try:
        post = await update_post(
            db,
            post_id,
            current_user.id,
            payload,
        )
    except PostNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        ) from error
    except PostPermissionDeniedError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the post author can update it",
        ) from error

    return PostResponse.model_validate(post)


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_post_endpoint(
    post_id: UUID,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> None:
    try:
        await delete_post(
            db,
            post_id,
            current_user.id,
        )
    except PostNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        ) from error
    except PostPermissionDeniedError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the post author can delete it",
        ) from error
