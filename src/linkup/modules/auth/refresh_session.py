from datetime import timedelta
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID

from redis.asyncio import Redis

from linkup.core.config import get_settings
from linkup.modules.auth.exceptions import InvalidRefreshTokenError

settings = get_settings()


def _refresh_key(refresh_token: str) -> str:
    token_hash = sha256(
        refresh_token.encode(),
    ).hexdigest()

    return f"auth:refresh:{token_hash}"


async def create_refresh_session(
    redis: Redis,
    user_id: UUID,
) -> str:
    refresh_token = token_urlsafe(32)

    await redis.set(
        _refresh_key(refresh_token),
        str(user_id),
        ex=timedelta(
            days=settings.refresh_token_expire_days,
        ),
    )
    return refresh_token


async def consume_refresh_session(
    redis: Redis,
    refresh_token: str,
) -> UUID:
    user_id_raw = await redis.getdel(
        _refresh_key(refresh_token),
    )

    if user_id_raw is None:
        raise InvalidRefreshTokenError

    if isinstance(user_id_raw, bytes):
        user_id_raw = user_id_raw.decode("utf-8")

    try:
        return UUID(user_id_raw)
    except ValueError as error:
        raise InvalidRefreshTokenError from error


async def revoke_refresh_session(
    redis: Redis,
    refresh_token: str,
) -> None:
    await redis.delete(
        _refresh_key(refresh_token),
    )
