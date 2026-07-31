from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    StringConstraints,
    field_validator,
)

CompanyName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=200,
    ),
]


def normalize_slug(value: object) -> object:
    if isinstance(value, str):
        return value.strip().lower()

    return value


CompanySlug = Annotated[
    str,
    BeforeValidator(normalize_slug),
    StringConstraints(
        min_length=1,
        max_length=120,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    ),
]

CompanyDescription = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
    ),
]

CompanyWebsite = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        max_length=2048,
    ),
]

CompanyLocation = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        max_length=255,
    ),
]

CompanyLogoURL = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        max_length=2048,
    ),
]


class CompanyCreate(BaseModel):
    name: CompanyName
    slug: CompanySlug
    description: CompanyDescription | None = None
    website: CompanyWebsite | None = None
    location: CompanyLocation | None = None
    logo_url: CompanyLogoURL | None = None


class CompanyUpdate(BaseModel):
    name: CompanyName | None = None
    slug: CompanySlug | None = None
    description: CompanyDescription | None = None
    website: CompanyWebsite | None = None
    location: CompanyLocation | None = None
    logo_url: CompanyLogoURL | None = None

    @field_validator(
        "name",
        "slug",
    )
    @classmethod
    def required_fields_cannot_be_null(
        cls,
        value: str | None,
    ) -> str:
        if value is None:
            raise ValueError("Field cannot be null")

        return value


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    name: str
    slug: str
    description: str | None
    website: str | None
    location: str | None
    logo_url: str | None
    created_at: datetime
    updated_at: datetime
