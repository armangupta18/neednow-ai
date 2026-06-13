from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.sustainability.agent import SustainabilityAgent
from app.agents.sustainability.retrieval_service import SustainabilityRetrievalService
from app.database.session import get_db
from app.services.sustainability_service import SustainabilityService


def get_sustainability_service(
    db: AsyncSession = Depends(get_db),
) -> SustainabilityService:
    retrieval_service = SustainabilityRetrievalService(db)
    sustainability_agent = SustainabilityAgent(retrieval_service)

    return SustainabilityService(
        sustainability_agent=sustainability_agent,
        db=db,
    )
