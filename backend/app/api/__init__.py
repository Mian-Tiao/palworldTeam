from fastapi import APIRouter

from app.api.activities import router as activities_router
from app.api.buff_matrix import router as buff_matrix_router
from app.api.elements import router as elements_router
from app.api.health import router as health_router
from app.api.pals import router as pals_router
from app.api.recommendations import router as recommendations_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(pals_router)
api_router.include_router(elements_router)
api_router.include_router(recommendations_router)
api_router.include_router(activities_router)
api_router.include_router(buff_matrix_router)
