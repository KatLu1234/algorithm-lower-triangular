from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Lower Triangular Project"
    
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # LLM (Upstage) — 시크릿은 이 파일 한 곳에서만 읽는다 (architecture.md §5.3).
    # 값은 .env 의 UPSTAGE_API_KEY 에서 로드된다 (.env 는 .gitignore 제외, 커밋/로그 금지).
    UPSTAGE_API_KEY: str = ""
    # OpenAI 호환 베이스 URL. 정확한 경로는 Upstage 공식 문서로 대조 후 확정할 것.
    UPSTAGE_BASE_URL: str = "https://api.upstage.ai/v1"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
