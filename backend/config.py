from pydantic_settings import BaseSettings
from typing import List
import os
import sys
import dotenv

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./data/skillhub.db"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    SKILLHUB_URL: str ="http://localhost:8000"
    SKILL_HOST: str = "0.0.0.0"
    SKILL_PORT: int = 8000
    ANTHROPIC_BASE_URL:str=""
    ANTHROPIC_AUTH_TOKEN:str=""

    class Config:
        env_file = ".env"

settings = Settings()
dotenv.load_dotenv()