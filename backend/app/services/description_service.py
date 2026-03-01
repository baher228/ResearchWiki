import json
import logging
import re
import asyncio

import boto3
from botocore.config import Config as BotoConfig

from app.config import get_settings
from app.prompt import DESCRIPTION_PROMPT

logger = logging.getLogger(__name__)

_BEDROCK_CONFIG = BotoConfig(read_timeout=600, connect_timeout=10)


def _get_bedrock_client():
    settings = get_settings()
    kwargs = {
        "region_name": settings.AWS_REGION,
        "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        "config": _BEDROCK_CONFIG,
    }
    if settings.AWS_SESSION_TOKEN:
        kwargs["aws_session_token"] = settings.AWS_SESSION_TOKEN
    return boto3.client("bedrock-runtime", **kwargs)


async def get_description(text: str) -> str:
    """Send highlighted text to Bedrock Mistral and return a description."""

    settings = get_settings()

    user_message = f"Summarize the following text into a description:\n\n{text}"

    model_id = settings.MISTRAL_MODEL_FAST
    logger.info("Sending text (%d chars) to Bedrock model %s", len(user_message), model_id)

    client = _get_bedrock_client()

    # Bedrock Mistral uses the Converse API
    response = client.converse(
        modelId=model_id,
        messages=[
            {
                "role": "user",
                "content": [
                    {"text": user_message}
                ],
            },
        ],
        system=[
            {"text": DESCRIPTION_PROMPT}
        ],
        inferenceConfig={
            "temperature": 0.3,
            "maxTokens": 8192,
        },
    )

    description = response["output"]["message"]["content"][0]["text"]

    logger.info("Received description response (%d chars)", len(description))

    return description