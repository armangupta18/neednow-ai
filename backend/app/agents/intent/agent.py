from app.services.gemini_service import (
    GeminiService,
)

from app.agents.intent.prompt import (
    INTENT_SYSTEM_PROMPT,
)

from app.agents.intent.parser import (
    IntentParser,
)

from app.agents.intent.schemas import (
    IntentResponse,
)


class IntentAgent:

    def __init__(
        self,
        llm_service: GeminiService,
    ):
        self.llm = llm_service

    async def analyze(
        self,
        user_input: str,
    ) -> IntentResponse:

        raw_response = await self.llm.invoke(
            system_prompt=INTENT_SYSTEM_PROMPT,
            user_prompt=user_input,
        )

        return IntentParser.parse(
            raw_response
        )