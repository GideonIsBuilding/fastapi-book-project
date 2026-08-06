import secrets

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "hng12-stage2"
    PROJECT_VERSION: str = "0.0.1"
    PROJECT_DESCRIPTION: str = "HNG12 DEVOPS x BACKEND (Stage 2)"
    API_PREFIX: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    DEBUG: bool = False
    TESTING: bool = False
    
    DATABASE_HOST: str = "db"
    DATABASE_PORT: int = 5432
    DATABASE_USER: str = ""
    DATABASE_PASSWORD: str = ""
    DATABASE_DB: str = "books"


settings = Settings()
