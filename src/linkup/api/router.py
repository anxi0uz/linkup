from fastapi import APIRouter

from linkup.modules.auth.router import router as ar
from linkup.modules.profiles.router import router as pr

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(ar)
api_router.include_router(pr)
