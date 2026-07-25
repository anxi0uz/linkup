from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from linkup.models import Profile
from linkup.modules.profiles.exceptions import ProfileNotFoundError
from linkup.modules.profiles.schemas import ProfileUpdate

log = structlog.get_logger(
    component="profiles.service",
)


async def update_profile(
    db: AsyncSession,
    profile: Profile,
    data: ProfileUpdate,
) -> Profile:
    updates = data.model_dump(
        exclude_unset=True,
    )

    if not updates:
        return profile

    for field, value in updates.items():
        setattr(
            profile,
            field,
            value,
        )

    await db.commit()
    await db.refresh(profile)

    log.info(
        "profile_updated",
        user_id=str(profile.user_id),
        changed_fields=sorted(updates),
    )

    return profile


async def get_profile_by_id(
    db: AsyncSession,
    user_id: UUID,
) -> Profile:
    prof = await db.get(Profile, user_id)

    if prof is None:
        raise ProfileNotFoundError

    return prof
