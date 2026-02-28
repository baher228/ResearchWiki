import json
import logging

from mistralai import Mistral

from app.config import get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert academic summarizer. Your job is to convert a research paper into a well-structured wiki-style page.

Return your response as a **valid JSON object** with the following structure — no markdown fences, no extra text, just raw JSON:

{
  "title": "A concise, descriptive wiki-style title",
  "summary": "A 2-3 sentence lead paragraph summarising the paper's purpose and key findings.",
  "sections": [
    {
      "title": "Section Heading",
      "content": "Markdown-formatted body of this section."
    }
  ]
}

Guidelines for the sections:
- Include at least these sections when applicable: Background, Objectives, Methodology, Key Findings, Discussion, Conclusion.
- Use clear, encyclopedic language accessible to a broad audience.
- Keep each section focused and concise while preserving essential details.
- Use markdown formatting (bold, lists, etc.) within section content for readability.
"""


async def summarize_paper(text: str) -> dict:
    """Send paper text to Mistral and return a structured wiki summary."""

    settings = get_settings()

    if not settings.MISTRAL_API_KEY or settings.MISTRAL_API_KEY == "your_mistral_api_key_here":
        raise ValueError(
            "MISTRAL_API_KEY is not configured. "
            "Please set a valid key in your .env file."
        )

    client = Mistral(api_key=settings.MISTRAL_API_KEY)

    logger.info("Sending paper (%d chars) to Mistral model %s", len(text), settings.MISTRAL_MODEL)

    response = await client.chat.complete_async(
        model=settings.MISTRAL_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Summarize the following research paper:\n\n{text}"},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    raw = response.choices[0].message.content
    logger.debug("Raw Mistral response: %s", raw[:500])

    result = json.loads(raw)
    return result
