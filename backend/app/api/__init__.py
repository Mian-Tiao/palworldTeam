from fastapi import APIRouter

from app.api.elements import router as elements_router
from app.api.health import router as health_router
from app.api.pals import router as pals_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(pals_router)
api_router.include_router(elements_router)
