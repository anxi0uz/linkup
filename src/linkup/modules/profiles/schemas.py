from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

Name = Annotated[
    str,
    Field(min_length=1, max_length=100),
]

Headline = Annotated[
    str,
    Field(max_length=220),
]

Location = Annotated[
    str,
    Field(max_length=255),
]

AvatarURL = Annotated[
    str,
    Field(max_length=2048),
]


class ProfileUpdate(BaseModel):
    first_name: Name | None = None
    last_name: Name | None = None
    headline: Headline | None = None
    about: str | None = None
    location: Location | None = None
    avatar_url: AvatarURL | None = None

    @field_validator(
        "first_name",
        "last_name",
    )
    @classmethod
    def names_cannot_be_null(
        cls,
        value: str | None,
    ) -> str:
        if value is None:
            raise ValueError("Name cannot be null")

        return value


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    first_name: str
    last_name: str
    headline: str | None
    about: str | None
    location: str | None
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime
