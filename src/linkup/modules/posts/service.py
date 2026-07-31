from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from linkup.models import Post
from linkup.modules.companies.service import (
    ensure_company_owner,
    get_company_by_id,
)
from linkup.modules.posts.exceptions import (
    PostNotFoundError,
    PostPermissionDeniedError,
)
from linkup.modules.posts.schemas import PostCreate, PostUpdate

log = structlog.get_logger(
    component="posts.service",
)


async def create_post(
    db: AsyncSession,
    author_id: UUID,
    data: PostCreate,
) -> Post:
    if data.company_id is not None:
        company = await get_company_by_id(
            db,
            data.company_id,
        )
        ensure_company_owner(
            company,
            author_id,
        )

    post = Post(
        **data.model_dump(),
        author_id=author_id,
    )

    db.add(post)
    await db.commit()
    await db.refresh(post)

    log.info(
        "post_created",
        post_id=str(post.id),
        author_id=str(author_id),
        company_id=(str(post.company_id) if post.company_id is not None else None),
    )

    return post


async def list_posts(
    db: AsyncSession,
    limit: int,
    offset: int,
    author_id: UUID | None = None,
    company_id: UUID | None = None,
) -> list[Post]:
    stmt = select(Post)

    if author_id is not None:
        stmt = stmt.where(Post.author_id == author_id)

    if company_id is not None:
        stmt = stmt.where(Post.company_id == company_id)

    posts = await db.scalars(
        stmt.order_by(
            Post.created_at.desc(),
            Post.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    return list(posts.all())


async def get_post_by_id(
    db: AsyncSession,
    post_id: UUID,
) -> Post:
    post = await db.get(Post, post_id)

    if post is None:
        raise PostNotFoundError

    return post


def ensure_post_author(
    post: Post,
    author_id: UUID,
) -> None:
    if post.author_id != author_id:
        raise PostPermissionDeniedError


async def update_post(
    db: AsyncSession,
    post_id: UUID,
    author_id: UUID,
    data: PostUpdate,
) -> Post:
    post = await get_post_by_id(
        db,
        post_id,
    )
    ensure_post_author(
        post,
        author_id,
    )

    updates = data.model_dump(
        exclude_unset=True,
    )

    if not updates:
        return post

    for field, value in updates.items():
        setattr(
            post,
            field,
            value,
        )

    await db.commit()
    await db.refresh(post)

    log.info(
        "post_updated",
        post_id=str(post.id),
        changed_fields=sorted(updates),
    )

    return post


async def delete_post(
    db: AsyncSession,
    post_id: UUID,
    author_id: UUID,
) -> None:
    post = await get_post_by_id(
        db,
        post_id,
    )
    ensure_post_author(
        post,
        author_id,
    )

    await db.delete(post)
    await db.commit()

    log.info(
        "post_deleted",
        post_id=str(post_id),
    )
