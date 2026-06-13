from fastapi import Depends

from app.agents.emergency.agent import EmergencyAgent
from app.agents.urgency.agent import UrgencyAgent
from app.dependencies.memory import get_memory_manager
from app.memory.memory_manager import MemoryManager
from app.services.bedrock_service import BedrockService
from app.services.emergency_service import EmergencyService


def get_emergency_service(
    memory_manager: MemoryManager = Depends(get_memory_manager),
) -> EmergencyService:
    bedrock = BedrockService()
    urgency_agent = UrgencyAgent(bedrock)
    emergency_agent = EmergencyAgent(urgency_agent)

    return EmergencyService(
        emergency_agent=emergency_agent,
        memory_manager=memory_manager,
    )
