from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db

from app.services.bedrock_service import (
    BedrockService,
)

from app.memory.memory_repository import (
    MemoryRepository,
)

from app.memory.memory_manager import (
    MemoryManager,
)

from app.agents.intent.agent import (
    IntentAgent,
)

from app.agents.urgency.agent import (
    UrgencyAgent,
)

from app.agents.product.agent import (
    ProductAgent,
)

from app.agents.sustainability.agent import (
    SustainabilityAgent,
)

from app.agents.supervisor.agent import (
    SupervisorAgent,
)

from app.agents.product.embedding_service import (
    EmbeddingService,
)

from app.agents.product.retrieval_service import (
    RetrievalService,
)

from app.agents.sustainability.retrieval_service import (
    SustainabilityRetrievalService,
)


def get_supervisor(
    db: AsyncSession = Depends(get_db),
) -> SupervisorAgent:

    bedrock = BedrockService()

    memory_repo = MemoryRepository(db)

    memory_manager = MemoryManager(
        memory_repo
    )

    intent_agent = IntentAgent(
        bedrock
    )

    urgency_agent = UrgencyAgent(
        bedrock
    )

    embedding_service = (
        EmbeddingService()
    )

    retrieval_service = (
        RetrievalService(
            db=db,
            index_path=
            "faiss_indexes/products.index",
        )
    )

    product_agent = ProductAgent(
        embedding_service=
        embedding_service,

        retrieval_service=
        retrieval_service,
    )

    sustainability_agent = (
        SustainabilityAgent(
            SustainabilityRetrievalService(
                db
            )
        )
    )

    return SupervisorAgent(
        intent_agent=
        intent_agent,

        urgency_agent=
        urgency_agent,

        product_agent=
        product_agent,

        sustainability_agent=
        sustainability_agent,

        memory_manager=
        memory_manager,
    )