from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Lower Triangular Project"
    
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
