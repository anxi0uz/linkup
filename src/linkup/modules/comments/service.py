from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from linkup.models import Comment
from linkup.modules.comments.exceptions import (
    CommentNotFoundError,
    CommentPermissionDeniedError,
)
from linkup.modules.comments.schemas import CommentCreate, CommentUpdate
from linkup.modules.posts.service import get_post_by_id

log = structlog.get_logger(
    component="comments.service",
)


async def create_comment(
    db: AsyncSession,
    post_id: UUID,
    author_id: UUID,
    data: CommentCreate,
) -> Comment:
    await get_post_by_id(db, post_id)

    comment = Comment(
        **data.model_dump(),
        author_id=author_id,
        post_id=post_id,
    )

    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    log.info(
        "comment_created",
        comment_id=str(comment.id),
        post_id=str(post_id),
        author_id=str(author_id),
    )

    return comment


async def list_comments(
    db: AsyncSession,
    post_id: UUID,
    offset: int,
    limit: int,
) -> list[Comment]:
    await get_post_by_id(db, post_id)

    comments = await db.scalars(
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(
            Comment.created_at.asc(),
            Comment.id.asc(),
        )
        .offset(offset)
        .limit(limit)
    )
    return list(comments.all())


async def get_comment_by_id(
    db: AsyncSession,
    comment_id: UUID,
) -> Comment:
    comment = await db.get(Comment, comment_id)

    if comment is None:
        raise CommentNotFoundError

    return comment


def ensure_comment_author(
    comment: Comment,
    author_id: UUID,
) -> None:
    if comment.author_id != author_id:
        raise CommentPermissionDeniedError


async def update_comment(
    db: AsyncSession,
    comment_id: UUID,
    author_id: UUID,
    data: CommentUpdate,
) -> Comment:
    comment = await get_comment_by_id(db, comment_id)
    ensure_comment_author(comment, author_id)

    updates = data.model_dump(exclude_unset=True)

    if not updates:
        return comment

    for field, value in updates.items():
        setattr(comment, field, value)

    await db.commit()
    await db.refresh(comment)

    log.info(
        "comment_updated",
        comment_id=str(comment.id),
        author_id=str(author_id),
        changed_fields=sorted(updates),
    )

    return comment


async def delete_comment(
    db: AsyncSession,
    comment_id: UUID,
    author_id: UUID,
) -> None:
    comment = await get_comment_by_id(db, comment_id)
    ensure_comment_author(comment, author_id)

    post_id = str(comment.post_id)
    comment_author_id = str(comment.author_id)

    await db.delete(comment)
    await db.commit()

    log.info(
        "comment_deleted",
        comment_id=str(comment_id),
        post_id=post_id,
        author_id=comment_author_id,
        deleted_by=str(author_id),
    )
