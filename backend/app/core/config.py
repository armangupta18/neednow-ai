"""Application configuration for NeedNow AI.

Loads environment variables from .env using Pydantic v2 BaseSettings.
Provides a singleton `settings` instance for use across the application.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Project
    PROJECT_NAME: str = "NeedNow AI"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Gemini
    GEMINI_API_KEY: str = ""

    # FAISS
    FAISS_INDEX_PATH: str = "data/faiss"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings: Settings = get_settings()
