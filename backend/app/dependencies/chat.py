from fastapi import Depends

from app.agents.supervisor.agent import SupervisorAgent
from app.dependencies.supervisor import get_supervisor
from app.services.chat_service import ChatService


def get_chat_service(
    supervisor: SupervisorAgent = Depends(get_supervisor),
) -> ChatService:
    return ChatService(supervisor=supervisor)
