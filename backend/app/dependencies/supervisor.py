"""Supervisor agent dependency injection for NeedNow AI.

Constructs the full supervisor agent pipeline with all sub-agents.
Handles missing FAISS indexes and service initialization errors
gracefully — the app continues in degraded mode rather than crashing.
"""

from __future__ import annotations

import logging

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.services.gemini_service import GeminiService
from app.memory.memory_repository import MemoryRepository
from app.memory.memory_manager import MemoryManager
from app.agents.intent.agent import IntentAgent
from app.agents.urgency.agent import UrgencyAgent
from app.agents.product.agent import ProductAgent
from app.agents.sustainability.agent import SustainabilityAgent
from app.agents.supervisor.agent import SupervisorAgent
from app.agents.product.embedding_service import EmbeddingService
from app.agents.product.retrieval_service import RetrievalService
from app.agents.sustainability.retrieval_service import SustainabilityRetrievalService

logger = logging.getLogger(__name__)


def get_supervisor(
    db: AsyncSession = Depends(get_db),
) -> SupervisorAgent:
    """Build the full SupervisorAgent with all sub-agents.

    Handles initialization errors for FAISS-dependent services
    gracefully — logs warnings and continues in degraded mode.
    All APIs remain functional; retrieval/recommendation may return
    empty results until indexes are generated.
    """

    # Core services
    llm = GeminiService()
    memory_repo = MemoryRepository(db)
    memory_manager = MemoryManager(memory_repo)

    # Intent & Urgency agents (no external dependencies)
    intent_agent = IntentAgent(llm)
    urgency_agent = UrgencyAgent(llm)

    # Product agent (depends on FAISS index — may not exist)
    try:
        embedding_service = EmbeddingService()
    except Exception as exc:
        logger.warning(
            "EmbeddingService initialization failed: %s. "
            "Product retrieval will return empty results.",
            exc,
        )
        embedding_service = EmbeddingService.__new__(EmbeddingService)
        embedding_service.client = None

    try:
        retrieval_service = RetrievalService(
            db=db,
            index_path="faiss_indexes/products.index",
        )
    except Exception as exc:
        logger.warning(
            "RetrievalService initialization failed: %s. "
            "Running in fallback mode — retrieval will return empty results.",
            exc,
        )
        # Create a minimal fallback instance
        retrieval_service = RetrievalService.__new__(RetrievalService)
        retrieval_service.db = db
        retrieval_service.index_path = "faiss_indexes/products.index"
        retrieval_service.index = None

    product_agent = ProductAgent(
        embedding_service=embedding_service,
        retrieval_service=retrieval_service,
        llm_service=llm,
    )

    # Sustainability agent
    try:
        sustainability_retrieval = SustainabilityRetrievalService(db)
        sustainability_agent = SustainabilityAgent(sustainability_retrieval)
    except Exception as exc:
        logger.warning(
            "SustainabilityAgent initialization failed: %s. "
            "Sustainability features will return empty results.",
            exc,
        )
        # Create a minimal fallback
        sustainability_agent = SustainabilityAgent.__new__(SustainabilityAgent)
        sustainability_agent.retrieval_service = None

    # Inject LLM into ReasoningBuilder for Gemini-powered reasoning
    from app.agents.supervisor.reasoning import ReasoningBuilder
    from app.agents.supervisor.conversation import ConversationBuilder
    ReasoningBuilder.set_llm(llm)
    ConversationBuilder.set_llm(llm)

    return SupervisorAgent(
        intent_agent=intent_agent,
        urgency_agent=urgency_agent,
        product_agent=product_agent,
        sustainability_agent=sustainability_agent,
        memory_manager=memory_manager,
    )
