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

    GEMINI_API_KEY: str = ""
    GEMINI_API_KEYS: List[str] = Field(default_factory=list)
    GEMINI_MODEL_ID: str = "gemini-2.5-flash"
    GEMINI_MAX_TOKENS: int = 2048
    GEMINI_TIMEOUT_SECONDS: int = 40  # Per-key timeout in seconds (configured for Gemini calls)

    @property
    def gemini_api_keys(self) -> List[str]:
        """Return list of non-empty Gemini API keys.
        Combines GEMINI_API_KEYS list, GEMINI_API_KEY_1..20 indexed vars,
        and comma-separated GEMINI_API_KEY string.
        """
        import os
        keys: list[str] = []
        if self.GEMINI_API_KEYS:
            keys.extend([k.strip() for k in self.GEMINI_API_KEYS if k and k.strip()])
        if self.GEMINI_API_KEY:
            keys.extend([k.strip() for k in self.GEMINI_API_KEY.split(",") if k and k.strip()])
        
        # Check indexed keys (GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.)
        for i in range(1, 21):
            val = os.getenv(f"GEMINI_API_KEY_{i}")
            if val and val.strip():
                keys.append(val.strip())

        seen = set()
        deduped = []
        for k in keys:
            if k not in seen:
                seen.add(k)
                deduped.append(k)
        return deduped

    FAISS_INDEX_PATH: str = "faiss_indexes"

    LOG_LEVEL: str = "INFO"

    MEMORY_TOP_K: int = 10

    VECTOR_TOP_K: int = 20

    SESSION_TTL_MINUTES: int = 60

    USE_MOCK_LLM: bool = True

    ENABLE_URGENCY_AGENT: bool = False
    ENABLE_SUSTAINABILITY_AGENT: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()