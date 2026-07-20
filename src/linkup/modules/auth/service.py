from dataclasses import dataclass

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from linkup.models import Profile, User
from linkup.modules.auth.exceptions import EmailAlreadyRegisteredError
from linkup.modules.auth.refresh_session import create_refresh_session
from linkup.modules.auth.schemas import RegisterRequest
from linkup.modules.auth.security import create_access_token, hash_password


@dataclass(slots=True)
class AuthResult:
    user: User
    access_token: str
    refresh_token: str


async def register(
    db: AsyncSession,
    data: RegisterRequest,
    redis: Redis,
) -> AuthResult:
    email = str(data.email).lower()
    stmt = select(User).where(User.email == email)
    existing_user = await db.scalar(stmt)

    if existing_user is not None:
        raise EmailAlreadyRegisteredError

    user = User(
        email=email,
        password_hash=hash_password(data.password),
        profile=Profile(
            first_name=data.first_name,
            last_name=data.last_name,
        ),
    )

    db.add(user)
    await db.flush()

    access_token = create_access_token(user.id)
    refresh_token = await create_refresh_session(
        redis,
        user.id,
    )

    await db.commit()

    return AuthResult(
        user=user,
        access_token=access_token,
        refresh_token=refresh_token,
    )
