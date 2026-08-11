from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from linkup.api.dependencies import SessionDep
from linkup.modules.auth.dependencies import CurrentUserDep
from linkup.modules.comments.exceptions import (
    CommentNotFoundError,
    CommentPermissionDeniedError,
)
from linkup.modules.comments.schemas import (
    CommentCreate,
    CommentResponse,
    CommentUpdate,
)
from linkup.modules.comments.service import (
    create_comment,
    delete_comment,
    list_comments,
    update_comment,
)
from linkup.modules.posts.exceptions import PostNotFoundError

router = APIRouter(
    tags=["Comments"],
)


@router.post(
    "/posts/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_comment(
    db: SessionDep,
    user: CurrentUserDep,
    payload: CommentCreate,
    post_id: UUID,
) -> CommentResponse:
    try:
        comment = await create_comment(
            db,
            post_id,
            user.id,
            payload,
        )
    except PostNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        ) from error

    return CommentResponse.model_validate(comment)


@router.get(
    "/posts/{post_id}/comments",
    response_model=list[CommentResponse],
)
async def get_comments(
    db: SessionDep,
    user: CurrentUserDep,
    post_id: UUID,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[CommentResponse]:

    try:
        comments = await list_comments(
            db,
            post_id,
            offset,
            limit,
        )
    except PostNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        ) from error

    return [CommentResponse.model_validate(comment) for comment in comments]


@router.patch(
    "/comments/{comment_id}",
    response_model=CommentResponse,
)
async def patch_comment(
    db: SessionDep,
    user: CurrentUserDep,
    comment_id: UUID,
    payload: CommentUpdate,
) -> CommentResponse:
    try:
        comment = await update_comment(
            db,
            comment_id,
            user.id,
            payload,
        )
    except CommentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        ) from error
    except CommentPermissionDeniedError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the comment author can update it",
        ) from error
    return CommentResponse.model_validate(comment)


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def del_comment(
    db: SessionDep,
    user: CurrentUserDep,
    comment_id: UUID,
) -> None:
    try:
        await delete_comment(db, comment_id, user.id)
    except CommentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        ) from error
    except CommentPermissionDeniedError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the comment author can delete it",
        ) from error
