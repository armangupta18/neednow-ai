from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.agents.urgency.agent import UrgencyAgent
from app.agents.urgency.schemas import UrgencyLevel, UrgencyResponse


class EmergencyAgent:
    """Coordinates emergency detection and escalation using the urgency agent."""

    _EMERGENCY_LEVELS = frozenset({UrgencyLevel.CRITICAL, UrgencyLevel.HIGH})
    _ESCALATION_SCORE_THRESHOLD = 90
    _EMERGENCY_SCORE_THRESHOLD = 70

    def __init__(self, urgency_agent: UrgencyAgent) -> None:
        self._urgency_agent = urgency_agent

    async def analyze(
        self,
        text: str,
        user_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        urgency = await self._urgency_agent.analyze(
            text=text,
            user_context=user_context,
        )

        is_emergency = (
            urgency.urgency in self._EMERGENCY_LEVELS
            or urgency.score >= self._EMERGENCY_SCORE_THRESHOLD
        )
        escalation_recommended = (
            urgency.urgency == UrgencyLevel.CRITICAL
            or urgency.score >= self._ESCALATION_SCORE_THRESHOLD
        )

        return {
            "urgency": urgency,
            "is_emergency": is_emergency,
            "escalation_recommended": escalation_recommended,
        }

    async def escalate(
        self,
        text: str,
        *,
        urgency: UrgencyResponse | None = None,
        user_context: dict[str, Any] | None = None,
        contact_phone: str | None = None,
    ) -> dict[str, Any]:
        if urgency is None:
            analysis = await self.analyze(text, user_context)
            urgency = analysis["urgency"]
            escalation_recommended = analysis["escalation_recommended"]
        else:
            escalation_recommended = (
                urgency.urgency == UrgencyLevel.CRITICAL
                or urgency.score >= self._ESCALATION_SCORE_THRESHOLD
            )

        if not escalation_recommended:
            return {
                "escalated": False,
                "urgency": urgency,
                "workflow_id": "",
                "message": "Situation does not require emergency escalation",
                "actions": [],
            }

        workflow_id = str(uuid4())
        actions = [
            "notify_on_call_support",
            "prioritize_fast_delivery_recommendations",
            "flag_supervisor_pipeline",
        ]

        if contact_phone:
            actions.append("queue_sms_alert")

        return {
            "escalated": True,
            "urgency": urgency,
            "workflow_id": workflow_id,
            "message": "Emergency workflow triggered successfully",
            "actions": actions,
        }
