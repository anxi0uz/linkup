from fastapi import APIRouter

from linkup.modules.auth.router import router as ar
from linkup.modules.companies.router import router as cr
from linkup.modules.posts.router import router as por
from linkup.modules.profiles.router import router as pr

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(ar)
api_router.include_router(pr)
api_router.include_router(cr)
api_router.include_router(por)
