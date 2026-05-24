from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Lower Triangular Project"

    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

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
