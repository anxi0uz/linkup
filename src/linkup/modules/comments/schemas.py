from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    StringConstraints,
    field_validator,
)

CommentContent = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=2000,
    ),
]


class CommentCreate(BaseModel):
    content: CommentContent


class CommentUpdate(BaseModel):
    content: CommentContent | None = None

    @field_validator("content")
    @classmethod
    def content_cannot_be_null(
        cls,
        value: str | None,
    ) -> str:
        if value is None:
            raise ValueError("Content cannot be null")

        return value


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    post_id: UUID
    author_id: UUID
    content: str
    created_at: datetime
    updated_at: datetime
