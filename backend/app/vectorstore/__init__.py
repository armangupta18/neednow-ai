"""Vector store package for NeedNow AI.

Provides FAISS-backed vector index management, index construction,
similarity retrieval, and synchronization utilities.

Usage:
    from app.vectorstore import FAISSManager, IndexBuilder, VectorRetriever, VectorSync
"""

from app.vectorstore.faiss_manager import FAISSManager
from app.vectorstore.index_builder import IndexBuilder
from app.vectorstore.retriever import VectorRetriever
from app.vectorstore.sync import VectorSync

__all__: list[str] = [
    "FAISSManager",
    "IndexBuilder",
    "VectorRetriever",
    "VectorSync",
]
