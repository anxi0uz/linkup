from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from linkup.db.base import Base

if TYPE_CHECKING:
    from linkup.models.post import Post
    from linkup.models.user import User


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )

    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
    )

    slug: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
    )

    website: Mapped[str | None] = mapped_column(
        String(2048),
    )

    location: Mapped[str | None] = mapped_column(
        String(255),
    )

    logo_url: Mapped[str | None] = mapped_column(
        String(2048),
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

    owner: Mapped["User"] = relationship(
        back_populates="owned_companies",
        lazy="raise",
    )

    posts: Mapped[list["Post"]] = relationship(
        back_populates="company",
        passive_deletes=True,
        lazy="raise",
    )
