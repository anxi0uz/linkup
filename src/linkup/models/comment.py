from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from linkup.db.base import Base

if TYPE_CHECKING:
    from linkup.models.post import Post
    from linkup.models.user import User


class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = (
        CheckConstraint(
            "char_length(content) BETWEEN 1 AND 2000",
            name="ck_comments_content_length",
        ),
        Index(
            "ix_comments_post_created_at",
            "post_id",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )

    post_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "posts.id",
            ondelete="CASCADE",
        ),
    )

    author_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
    )

    content: Mapped[str] = mapped_column(
        Text,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    post: Mapped["Post"] = relationship(
        back_populates="comments",
        lazy="raise",
    )

    author: Mapped["User"] = relationship(
        back_populates="comments",
        lazy="raise",
    )
