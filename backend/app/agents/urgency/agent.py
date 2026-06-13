from datetime import datetime

from app.services.bedrock_service import (
    BedrockService,
)

from app.agents.urgency.prompt import (
    URGENCY_SYSTEM_PROMPT,
)

from app.agents.urgency.parser import (
    UrgencyParser,
)

from app.agents.urgency.schemas import (
    UrgencyResponse,
    UrgencyLevel,
)

from app.agents.urgency.rules import (
    UrgencyRules,
)


class UrgencyAgent:

    def __init__(
        self,
        bedrock_service: BedrockService,
    ):
        self.bedrock = bedrock_service

    async def analyze(
        self,
        text: str,
        user_context: dict | None = None,
    ) -> UrgencyResponse:

        current_hour = datetime.now().hour

        prompt = f"""
User Situation:
{text}

Current Hour:
{current_hour}

User Context:
{user_context}
"""

        response = await self.bedrock.invoke(
            system_prompt=URGENCY_SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        urgency = UrgencyParser.parse(
            response
        )

        adjusted_score = UrgencyRules.boost_score(
            text=text,
            score=urgency.score,
        )

        adjusted_score = (
            UrgencyRules.time_of_day_adjustment(
                adjusted_score,
                current_hour,
            )
        )

        final_level = self._calculate_level(
            adjusted_score
        )

        return UrgencyResponse(
            urgency=final_level,
            score=adjusted_score,
            explanation=urgency.explanation,
        )

    @staticmethod
    def _calculate_level(
        score: int,
    ) -> UrgencyLevel:

        if score >= 90:
            return UrgencyLevel.CRITICAL

        if score >= 70:
            return UrgencyLevel.HIGH

        if score >= 40:
            return UrgencyLevel.MEDIUM

        return UrgencyLevel.LOW