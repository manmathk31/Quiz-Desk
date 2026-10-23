"""Core application configuration and settings."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Quizdesk API"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    # PostgreSQL Database URL (psycopg3 driver)
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/quizdesk"

    # CORS Allowed Origins (Restricted list; no wildcard in production)
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Supabase Auth & JWT Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None
    SUPABASE_JWT_PUBLIC_KEY: Optional[str] = None
    SUPABASE_JWT_ALGORITHM: str = "HS256"
    SUPABASE_JWT_AUDIENCE: Optional[str] = "authenticated"
    SUPABASE_JWT_ISSUER: Optional[str] = None

    # Operational & Deployment Environment (DEC-022)
    ENVIRONMENT: str = "development"
    ALLOW_DESTRUCTIVE_RESET: bool = False

    # Administrator Provisioning (DEC-022)
    ADMIN_EMAIL: Optional[str] = None
    ADMIN_NAME: Optional[str] = "System Administrator"
    ADMIN_BOOTSTRAP_TOKEN: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
