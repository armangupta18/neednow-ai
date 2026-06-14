from __future__ import annotations

from uuid import UUID

from app.agents.emergency.agent import EmergencyAgent
from app.memory.memory_manager import MemoryManager
from app.schemas.emergency import (
    EmergencyAnalyzeResponse,
    EmergencyEscalateResponse,
    EmergencyHealthResponse,
)


class EmergencyService:
    """Service layer for emergency analysis and escalation workflows."""

    def __init__(
        self,
        emergency_agent: EmergencyAgent,
        memory_manager: MemoryManager | None = None,
    ) -> None:
        self._emergency_agent = emergency_agent
        self._memory_manager = memory_manager

    async def analyze_urgency(
        self,
        *,
        user_id: UUID,
        text: str,
        user_context: dict | None = None,
    ) -> EmergencyAnalyzeResponse:
        context = await self._resolve_user_context(user_id, user_context)
        result = await self._emergency_agent.analyze(text=text, user_context=context)
        urgency = result["urgency"]

        return EmergencyAnalyzeResponse(
            user_id=user_id,
            urgency=urgency.urgency,
            score=urgency.score,
            explanation=urgency.explanation,
            is_emergency=result["is_emergency"],
            escalation_recommended=result["escalation_recommended"],
        )

    async def escalate_emergency(
        self,
        *,
        user_id: UUID,
        text: str,
        user_context: dict | None = None,
        contact_phone: str | None = None,
    ) -> EmergencyEscalateResponse:
        context = await self._resolve_user_context(user_id, user_context)
        analysis = await self._emergency_agent.analyze(text=text, user_context=context)
        result = await self._emergency_agent.escalate(
            text=text,
            urgency=analysis["urgency"],
            user_context=context,
            contact_phone=contact_phone,
        )
        urgency = result["urgency"]

        return EmergencyEscalateResponse(
            user_id=user_id,
            escalated=result["escalated"],
            urgency=urgency.urgency,
            score=urgency.score,
            workflow_id=result["workflow_id"],
            message=result["message"],
            actions=result["actions"],
        )

    def health_check(self) -> EmergencyHealthResponse:
        return EmergencyHealthResponse(
            status="healthy",
            urgency_agent="available",
            emergency_agent="available",
        )

    async def _resolve_user_context(
        self,
        user_id: UUID,
        user_context: dict | None,
    ) -> dict:
        if user_context is not None:
            return user_context

        if self._memory_manager is None:
            return {}

        try:
            memory = await self._memory_manager.retrieve_memory(user_id)
            return memory.model_dump()
        except Exception:
            return {}
