from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from linkup.api.dependencies import SessionDep
from linkup.modules.auth.dependencies import CurrentUserDep
from linkup.modules.profiles.exceptions import ProfileNotFoundError
from linkup.modules.profiles.schemas import ProfileResponse, ProfileUpdate
from linkup.modules.profiles.service import get_profile_by_id, update_profile

router = APIRouter(
    prefix="/profile",
    tags=["Profiles"],
)


@router.patch(
    "/me",
    response_model=ProfileResponse,
)
async def update_my_profile(
    payload: ProfileUpdate,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> ProfileResponse:
    profile = await update_profile(
        db,
        current_user.profile,
        payload,
    )

    return ProfileResponse.model_validate(
        profile,
    )


@router.get(
    "/{profile_id}",
    response_model=ProfileResponse,
)
async def get_profile(
    profile_id: UUID,
    db: SessionDep,
    current_user: CurrentUserDep,
) -> ProfileResponse:

    try:
        profile = await get_profile_by_id(db, profile_id)
    except ProfileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        ) from error
    return ProfileResponse.model_validate(profile)
