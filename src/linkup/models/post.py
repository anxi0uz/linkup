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
    from linkup.models.company import Company
    from linkup.models.user import User


class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (
        CheckConstraint(
            "char_length(content) BETWEEN 1 AND 3000",
            name="ck_posts_content_length",
        ),
        Index(
            "ix_posts_author_created_at",
            "author_id",
            "created_at",
        ),
        Index(
            "ix_posts_company_created_at",
            "company_id",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )

    author_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
    )

    company_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "companies.id",
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

    author: Mapped["User"] = relationship(
        back_populates="posts",
        lazy="raise",
    )

    company: Mapped["Company | None"] = relationship(
        back_populates="posts",
        lazy="raise",
    )
