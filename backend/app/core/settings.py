from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "NeedNow AI"
    APP_VERSION: str = "1.0.0"

    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    API_PREFIX: str = "/api/v1"

    SECRET_KEY: str

    DATABASE_URL: str

    ALLOWED_ORIGINS: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://10.26.29.116:3000",
            "http://10.55.97.116:3000",
            "*",
        ]
    )

    AWS_REGION: str = "ap-south-1"

    BEDROCK_MODEL_ID: str = (
        "anthropic.claude-3-5-sonnet-20241022-v2:0"
    )

    BEDROCK_MAX_TOKENS: int = 4096

    FAISS_INDEX_PATH: str = "faiss_indexes"

    LOG_LEVEL: str = "INFO"

    MEMORY_TOP_K: int = 10

    VECTOR_TOP_K: int = 20

    SESSION_TTL_MINUTES: int = 60

    USE_MOCK_LLM: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()