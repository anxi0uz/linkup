from fastapi import APIRouter, Response, status

from linkup.api.dependencies import RedisDep, SessionDep
from linkup.modules.auth.schemas import AuthResponse, RegisterRequest
from linkup.modules.auth.service import register

router = APIRouter(
    prefix="/auth",
    tags=["Users"],
)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    payload: RegisterRequest,
    db: SessionDep,
    redis: RedisDep,
    response: Response,
):
    result = await register(db, payload, redis)

    response.set_cookie(
        key="refresh_token",
        value=result.refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/api/v1/auth",
        max_age=30 * 24 * 60 * 60,
    )
    return AuthResponse.model_validate(
        {
            "access_token": result.access_token,
            "user": result.user,
        },
    )
