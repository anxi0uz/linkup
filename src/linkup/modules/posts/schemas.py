from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    StringConstraints,
    field_validator,
)

PostContent = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=3000,
    ),
]


class PostCreate(BaseModel):
    content: PostContent
    company_id: UUID | None = None


class PostUpdate(BaseModel):
    content: PostContent | None = None

    @field_validator("content")
    @classmethod
    def content_cannot_be_null(
        cls,
        value: str | None,
    ) -> str:
        if value is None:
            raise ValueError("Content cannot be null")

        return value


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    author_id: UUID
    company_id: UUID | None
    content: str
    created_at: datetime
    updated_at: datetime
