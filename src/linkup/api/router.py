from fastapi import APIRouter

from linkup.modules.auth.router import router as ar

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(ar)
