from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from linkup.db.base import Base

if TYPE_CHECKING:
    from linkup.models.user import User


class Profile(Base):
    __tablename__ = "profiles"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
    )

    headline: Mapped[str | None] = mapped_column(
        String(220),
    )

    about: Mapped[str | None] = mapped_column(
        Text,
    )

    location: Mapped[str | None] = mapped_column(
        String(255),
    )

    avatar_url: Mapped[str | None] = mapped_column(
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

    user: Mapped["User"] = relationship(
        back_populates="profile",
    )
