from __future__ import annotations

from uuid import UUID, uuid4

from app.agents.shared.message import AgentMessage, MessageRole
from app.agents.supervisor.agent import SupervisorAgent
from app.agents.supervisor.exception import SupervisorException
from app.schemas.chat import ChatHistoryResponse, ChatRequest, ChatResponse


class ChatService:
    """Orchestrates conversational chat turns through the supervisor pipeline."""

    def __init__(self, supervisor: SupervisorAgent) -> None:
        self._supervisor = supervisor
        self._sessions: dict[UUID, list[AgentMessage]] = {}

    async def process_message(self, request: ChatRequest) -> ChatResponse:
        session_id = request.session_id or uuid4()

        user_message = AgentMessage(
            user_id=request.user_id,
            session_id=session_id,
            content=request.message,
            role=MessageRole.USER,
        )
        self._append_message(session_id, user_message)

        try:
            result = await self._supervisor.execute(
                user_id=request.user_id,
                situation=request.message,
            )
        except ValueError as exc:
            raise exc
        except SupervisorException as exc:
            raise RuntimeError(str(exc)) from exc

        assistant_message = AgentMessage(
            user_id=request.user_id,
            session_id=session_id,
            content=result.reasoning,
            role=MessageRole.ASSISTANT,
            metadata={
                "urgency_level": result.urgency.get("level"),
                "confidence": result.metadata.get("confidence"),
            },
        )
        self._append_message(session_id, assistant_message)

        return ChatResponse(
            session_id=session_id,
            user_message=user_message,
            assistant_message=assistant_message,
            cart=result.cart,
            urgency=result.urgency,
            reasoning=result.reasoning,
            eco_alternative=result.eco_alternative,
            metadata=result.metadata,
        )

    def get_history(
        self,
        *,
        session_id: UUID,
        user_id: UUID,
    ) -> ChatHistoryResponse:
        messages = list(self._sessions.get(session_id, []))
        if messages and messages[0].user_id != user_id:
            raise PermissionError("Session does not belong to the requested user")

        return ChatHistoryResponse(
            session_id=session_id,
            user_id=user_id,
            messages=messages,
        )

    def _append_message(
        self,
        session_id: UUID,
        message: AgentMessage,
    ) -> None:
        self._sessions.setdefault(session_id, []).append(message)
