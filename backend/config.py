from pydantic_settings import BaseSettings
from typing import List
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
    GATEWAY_FORCE_PLAINTEXT: bool = False
    SKIP_VERIFY: bool = False
    AUDIT_LOG_RETENTION_DAYS: int = 120

    # Aegis Portal OIDC client settings. The browser-facing issuer and the
    # container-reachable backchannel can be different in Docker deployments.
    OIDC_ISSUER: str = "http://127.0.0.1:8080"
    OIDC_BACKCHANNEL_URL: str = "http://127.0.0.1:8000"
    OIDC_CLIENT_ID: str = ""
    OIDC_CLIENT_SECRET: str = ""
    OIDC_REDIRECT_URI: str = "http://127.0.0.1/api/v1/sso/callback"
    OIDC_POST_LOGIN_REDIRECT: str = "/sso/callback"
    OIDC_TRANSACTION_TTL_SECONDS: int = 300
    OIDC_TICKET_TTL_SECONDS: int = 60
    OIDC_SECURE_COOKIE: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
dotenv.load_dotenv()
