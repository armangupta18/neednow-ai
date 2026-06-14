"""Embeddings package for NeedNow AI.

Provides text chunking, vector embedding generation, and similarity-based
retrieval for the memory subsystem.

Usage:
    from app.memory.embeddings import Embedder, TextChunker, EmbeddingRetriever
"""

from app.memory.embeddings.chunker import TextChunker
from app.memory.embeddings.embedder import Embedder
from app.memory.embeddings.retrieval import EmbeddingRetriever

__all__: list[str] = [
    "Embedder",
    "TextChunker",
    "EmbeddingRetriever",
]
