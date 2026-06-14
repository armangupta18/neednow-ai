"""Product embedding service.

Generates text embeddings for product search.
Uses a deterministic local embedding approach for development
and can integrate with Google Gemini embedding API when available.
"""

import hashlib
import json
import logging

from app.core.settings import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 128  # Dimension for local embeddings


class EmbeddingService:

    def __init__(self) -> None:
        self._mock_mode = settings.USE_MOCK_LLM
        self._model = None

        if self._mock_mode:
            logger.info("EmbeddingService initialized in MOCK mode (local embeddings)")
        else:
            try:
                import google.generativeai as genai

                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._model = genai
                logger.info("EmbeddingService initialized with Google Gemini Embedding")
            except Exception as exc:
                logger.warning(
                    "Failed to initialize Gemini embedding client: %s. Using local embeddings.",
                    exc,
                )
                self._mock_mode = True

    async def generate_embedding(
        self,
        text: str,
    ) -> list[float]:
        """Generate an embedding vector for text.

        In mock mode: returns a deterministic 128-dim vector based on text hash.
        In Gemini mode: calls Google text-embedding model.
        """
        if self._mock_mode:
            return self._mock_embedding(text)

        try:
            result = self._model.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document",
            )
            return result["embedding"]

        except Exception as exc:
            logger.warning("Gemini embedding failed: %s. Using local fallback.", exc)
            return self._mock_embedding(text)

    @staticmethod
    def _mock_embedding(text: str) -> list[float]:
        """Generate a deterministic embedding from text using MD5 hash.

        Same text always produces the same vector — enables consistent
        retrieval behavior during development.
        """
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16)
        return [
            ((seed >> i) & 255) / 255.0
            for i in range(EMBEDDING_DIM)
        ]
