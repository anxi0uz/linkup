import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import linkup.models
from linkup.db.base import Base
from linkup.db.redis import get_redis
from linkup.db.session import get_session
from linkup.main import app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://linkup:linkup@127.0.0.1:5433/linkup_test",
)

TEST_REDIS_URL = os.getenv(
    "TEST_REDIS_URL",
    "redis://127.0.0.1:6380/0",
)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine]:
    engine = create_async_engine(
        TEST_DATABASE_URL,
        pool_pre_ping=True,
    )

    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.drop_all,
        )
        await connection.run_sync(
            Base.metadata.create_all,
        )
    try:
        yield engine
    finally:
        async with engine.begin() as connection:
            await connection.run_sync(
                Base.metadata.drop_all,
            )

        await engine.dispose()


@pytest.fixture
async def test_redis() -> AsyncGenerator[Redis]:
    redis = Redis.from_url(
        TEST_REDIS_URL,
        decode_responses=True,
    )

    await redis.flushdb()

    try:
        yield redis
    finally:
        await redis.flushdb()
        await redis.aclose()


@pytest.fixture
async def client(
    test_engine: AsyncEngine,
    test_redis: Redis,
) -> AsyncGenerator[AsyncClient]:
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        autoflush=False,
        expire_on_commit=False,
    )

    async def override_get_session() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    async def override_get_redis() -> Redis:
        return test_redis

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_redis] = override_get_redis

    transport = ASGITransport(
        app=app,
        raise_app_exceptions=True,
    )

    try:
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as http_client:
            yield http_client
    finally:
        app.dependency_overrides.clear()
