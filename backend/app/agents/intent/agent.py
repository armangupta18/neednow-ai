from app.services.bedrock_service import (
    BedrockService,
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
        bedrock_service: BedrockService,
    ):
        self.bedrock = bedrock_service

    async def analyze(
        self,
        user_input: str,
    ) -> IntentResponse:

        raw_response = await self.bedrock.invoke(
            system_prompt=INTENT_SYSTEM_PROMPT,
            user_prompt=user_input,
        )

        return IntentParser.parse(
            raw_response
        )