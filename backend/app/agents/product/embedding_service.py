"""Product embedding service.

Generates text embeddings for product search.
Supports mock mode (deterministic local embeddings) and
Bedrock mode (Amazon Titan Embed).
"""

import hashlib
import json
import logging

from app.core.settings import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 128  # Dimension for mock embeddings


class EmbeddingService:

    def __init__(self) -> None:
        self._mock_mode = settings.USE_MOCK_LLM
        self._client = None

        if self._mock_mode:
            logger.info("EmbeddingService initialized in MOCK mode (local embeddings)")
        else:
            try:
                import boto3
                self._client = boto3.client(
                    "bedrock-runtime",
                    region_name=settings.AWS_REGION,
                )
                logger.info("EmbeddingService initialized with Amazon Titan Embed")
            except Exception as exc:
                logger.warning(
                    "Failed to initialize Bedrock client: %s. Using mock embeddings.", exc
                )
                self._mock_mode = True

    async def generate_embedding(
        self,
        text: str,
    ) -> list[float]:
        """Generate an embedding vector for text.

        In mock mode: returns a deterministic 128-dim vector based on text hash.
        In Bedrock mode: calls Amazon Titan Embed v2.
        """
        if self._mock_mode:
            return self._mock_embedding(text)

        try:
            body = {"inputText": text}

            response = self._client.invoke_model(
                modelId="amazon.titan-embed-text-v2:0",
                body=json.dumps(body),
            )

            result = json.loads(response["body"].read())
            return result["embedding"]

        except Exception as exc:
            logger.warning("Bedrock embedding failed: %s. Using mock.", exc)
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
