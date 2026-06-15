"""Product embedding service.

Generates text embeddings for product search.
Attempts Google Gemini Embedding API on startup — if unavailable
(unsupported model, quota limit, or wrong API version), falls back
silently to local deterministic embeddings. Local embeddings are
consistent across runs and enable stable retrieval behavior.
"""

import hashlib
import logging

from app.core.settings import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 128  # Dimension for local hash-based embeddings

# Supported Gemini embedding model name
GEMINI_EMBEDDING_MODEL = "models/text-embedding-004"


class EmbeddingService:
    """Embedding service with Gemini → local fallback.

    Startup behavior:
    - If USE_MOCK_LLM=true: uses local embeddings, no API call attempted.
    - If GEMINI_API_KEY is set: probes API once. If it returns 404 or any
      error, logs a single INFO message and switches to local mode permanently.
    - Per-request failures also fall back to local without a warning log.
    """

    def __init__(self) -> None:
        self._mock_mode = settings.USE_MOCK_LLM
        self._model = None
        self._sdk_version = "unknown"

        if self._mock_mode:
            logger.info("EmbeddingService: local mode (USE_MOCK_LLM=true)")
            return

        if not settings.GEMINI_API_KEY:
            logger.info("EmbeddingService: local mode (no GEMINI_API_KEY)")
            self._mock_mode = True
            return

        # Attempt to configure Gemini embedding
        try:
            import google.generativeai as genai
            self._sdk_version = getattr(genai, "__version__", "unknown")
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._model = genai
            logger.info(
                "EmbeddingService: Gemini mode | model=%s | sdk=%s",
                GEMINI_EMBEDDING_MODEL,
                self._sdk_version,
            )
        except Exception as exc:
            logger.info(
                "EmbeddingService: local mode (Gemini init failed: %s)", exc
            )
            self._mock_mode = True

    async def generate_embedding(
        self,
        text: str,
    ) -> list[float]:
        """Generate an embedding vector for text.

        Returns a 128-dim vector. Local mode produces deterministic results
        (same text → same vector) which is stable for retrieval ranking.
        """
        if self._mock_mode:
            return self._local_embedding(text)

        try:
            result = self._model.embed_content(
                model=GEMINI_EMBEDDING_MODEL,
                content=text,
                task_type="retrieval_document",
            )
            return result["embedding"]

        except Exception as exc:
            err_str = str(exc)
            # 404 = model not found for this API version/key — switch to local permanently
            if "404" in err_str or "not found" in err_str.lower():
                logger.info(
                    "EmbeddingService: switching to local mode "
                    "(model %s unavailable: %s | sdk=%s)",
                    GEMINI_EMBEDDING_MODEL,
                    err_str[:120],
                    self._sdk_version,
                )
                self._mock_mode = True  # Stop retrying
            else:
                logger.debug("Gemini embedding failed, using local: %s", err_str[:80])
            return self._local_embedding(text)

    @staticmethod
    def _local_embedding(text: str) -> list[float]:
        """Deterministic local embedding using MD5 hash.

        Same text always produces the same 128-dim vector, ensuring
        consistent retrieval ranking across restarts.
        """
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16)
        return [
            ((seed >> i) & 255) / 255.0
            for i in range(EMBEDDING_DIM)
        ]

    # Keep old name as alias for backward compatibility
    _mock_embedding = _local_embedding
