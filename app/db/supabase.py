"""Supabase 클라이언트 — 지연 초기화.

SUPABASE_URL·SUPABASE_KEY 미설정 시 import 단계가 죽지 않도록 첫 사용 시점에서
클라이언트를 생성한다. DB 연결이 없어도 알고리즘·시간표 라우트는 동작해야 함
(MVP — 시간표 API는 DB와 무관).
"""
from typing import Optional

from supabase import Client, create_client

from app.core.config import settings

_client: Optional[Client] = None


def _ensure_client() -> Client:
    global _client
    if _client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise RuntimeError(
                "Supabase 클라이언트 사용 전에 SUPABASE_URL·SUPABASE_KEY 환경변수를 설정하세요."
            )
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _client


class _LazyClientProxy:
    """기존 `from app.db.supabase import supabase` 사용처와 호환."""

    def __getattr__(self, name: str):
        return getattr(_ensure_client(), name)


supabase = _LazyClientProxy()
