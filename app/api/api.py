from fastapi import APIRouter
from app.api.endpoints import items, timetable, utils

api_router = APIRouter()
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(timetable.router, prefix="/timetable", tags=["timetable"])
