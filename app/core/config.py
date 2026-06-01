from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Lower Triangular Project"

    # service_role(Secret) 키. RLS를 우회해 카탈로그 적재·결과 기록에 사용.
    # 외부 노출 금지(server/db/auth-and-rls.md §2).
    # 인증(로그인/회원가입)은 Supabase 가 아니라 로컬 SQLite 에 보관한다
    # (app/libs/auth_store.py — AUTH_DB_PATH).
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # 로컬 인증 저장소(SQLite) 경로. 상대경로면 프로젝트 루트 기준.
    # 운영 시 디스크 경로(예: /var/lib/lt/auth.db)로 덮어쓰기.
    AUTH_DB_PATH: str = "data/auth.db"

    # Upstage Solar API (자연어 → PreferenceVector delta).
    # 키가 비어 있으면 LLM 라우트는 503 LLM_UNAVAILABLE 응답.
    UPSTAGE_API_KEY: str = ""
    UPSTAGE_API_URL: str = "https://api.upstage.ai/v1/chat/completions"
    UPSTAGE_MODEL: str = "solar-pro2"
    UPSTAGE_TIMEOUT_S: float = 12.0

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
