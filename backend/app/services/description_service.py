import json
import logging
from urllib import request, error

from app.config import get_settings
from app.prompt import DESCRIPTION_PROMPT

logger = logging.getLogger(__name__)


def _extract_text_content(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(str(text))
        return "\n".join(parts).strip()
    return ""


def _mistral_chat_completion(*, model: str, user_message: str, temperature: float, max_tokens: int) -> str:
    settings = get_settings()
    if not settings.MISTRAL_API_KEY:
        raise RuntimeError("MISTRAL_API_KEY is not set")

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    body = json.dumps(payload).encode("utf-8")

    req = request.Request(
        "https://api.mistral.ai/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {settings.MISTRAL_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=120) as resp:
            response_data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Mistral API HTTP {e.code}: {detail}") from e
    except error.URLError as e:
        raise RuntimeError(f"Mistral API network error: {e}") from e

    choices = response_data.get("choices") or []
    if not choices:
        raise RuntimeError("Mistral API returned no choices")

    message = choices[0].get("message") or {}
    content = _extract_text_content(message.get("content"))
    if not content:
        raise RuntimeError("Mistral API returned empty message content")
    return content


async def get_description(text: str) -> str:
    """Send highlighted text to Mistral API and return a description."""

    settings = get_settings()

    user_message = f"{DESCRIPTION_PROMPT.strip()}\n\nSummarize the following text into a description:\n\n{text}"

    model_id = settings.MISTRAL_FAST_MODEL
    logger.info("Sending text (%d chars) to Mistral model %s", len(user_message), model_id)

    description = _mistral_chat_completion(
        model=model_id,
        user_message=user_message,
        temperature=0.3,
        max_tokens=8192,
    )

    logger.info("Received description response (%d chars)", len(description))

    return description