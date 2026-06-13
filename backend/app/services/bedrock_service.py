import json

import boto3

from app.core.settings import settings


class BedrockService:

    def __init__(self):

        self.client = boto3.client(
            "bedrock-runtime",
            region_name=settings.AWS_REGION,
        )

    async def invoke(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": 0.1,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
        }

        response = self.client.invoke_model(
            modelId=settings.BEDROCK_MODEL_ID,
            body=json.dumps(body),
        )

        response_body = json.loads(
            response["body"].read()
        )

        return response_body["content"][0]["text"]