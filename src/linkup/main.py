from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from linkup.api.middleware import RequestLoggingMiddleware
from linkup.api.router import api_router
from linkup.core.config import get_settings
from linkup.core.logger import configure_loggin
from linkup.db.redis import close_redis
from linkup.db.session import engine

settings = get_settings()

configure_loggin(settings.debug)

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncGenerator[None]:
    log.info("application_started")

    yield

    log.info("application_stopping")

    await close_redis()
    await engine.dispose()

    log.info("application_stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(RequestLoggingMiddleware)
    app.include_router(api_router)

    @app.get("/health", tags=["system"])
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
