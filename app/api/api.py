from fastapi import APIRouter
# items 라우터는 supabase 의존 — MVP 프로토타입에서는 비활성화.
# Supabase 연결 후 아래 import 의 items 와 include_router 한 줄을 복구하면 됨.
from app.api.endpoints import auth, timetable, utils

api_router = APIRouter()
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
# api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(timetable.router, prefix="/timetable", tags=["timetable"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
