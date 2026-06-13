import json
import boto3

from app.core.settings import settings


class EmbeddingService:

    def __init__(self):

        self.client = boto3.client(
            "bedrock-runtime",
            region_name=settings.AWS_REGION,
        )

    async def generate_embedding(
        self,
        text: str,
    ) -> list[float]:

        body = {
            "inputText": text
        }

        response = self.client.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            body=json.dumps(body),
        )

        result = json.loads(
            response["body"].read()
        )

        return result["embedding"]