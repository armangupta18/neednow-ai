"""Workers package for NeedNow AI.

Provides async background workers for memory synchronization, embedding
generation, recommendation pre-computation, and sustainability scoring.

Usage:
    from app.workers import (
        MemorySyncWorker,
        EmbeddingWorker,
        RecommendationWorker,
        SustainabilityWorker,
    )
"""

from app.workers.embedding_worker import EmbeddingWorker
from app.workers.memory_sync import MemorySyncWorker
from app.workers.recommendation_worker import RecommendationWorker
from app.workers.sustainability_worker import SustainabilityWorker

__all__: list[str] = [
    "MemorySyncWorker",
    "EmbeddingWorker",
    "RecommendationWorker",
    "SustainabilityWorker",
]
