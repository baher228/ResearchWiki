import json
import logging
import re
import asyncio

import boto3
from botocore.config import Config as BotoConfig

from app.config import get_settings
from app.prompt import SYSTEM_PROMPT

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


def _extract_image_info(paper_text: str) -> list[dict]:
    """Extract image paths and their surrounding context from the parsed markdown."""
    images = []
    lines = paper_text.split("\n")
    for i, line in enumerate(lines):
        match = re.search(r'!\[([^\]]*)\]\(([^)]+)\)', line)
        if match:
            alt_text = match.group(1)
            path = match.group(2).replace('\\', '/')
            context_start = max(0, i - 2)
            context_end = min(len(lines), i + 5)
            context = "\n".join(lines[context_start:context_end])
            images.append({
                "index": len(images),
                "path": path,
                "alt": alt_text,
                "context": context,
            })
    return images


def _build_image_list_text(images: list[dict]) -> str:
    """Build a text block listing available images with context."""
    if not images:
        return ""
    parts = ["\n\n---\nAVAILABLE FIGURES (extracted from the PDF):\n"]
    for img in images:
        fig_match = re.search(r'(?:Figure|Fig\.?)\s+(\d+)', img["context"], re.IGNORECASE)
        fig_label = f"Figure {fig_match.group(1)}" if fig_match else f"Image {img['index'] + 1}"
        parts.append(f"- FIGURE_{img['index']}: {fig_label}")
        caption_lines = [l.strip() for l in img["context"].split("\n") if l.strip() and not l.strip().startswith("![")]
        if caption_lines:
            parts.append(f"  Context: {' '.join(caption_lines[:2])}")
    return "\n".join(parts)


def post_process_images(summary: str, images: list[dict]) -> str:
    """Replace image placeholders in the summary with actual image paths."""
    for img in images:
        # First, safely replace exact FIGURE_N placeholders using lambda to avoid escape char bugs
        pattern_exact = r"\bFIGURE_" + str(img['index']) + r"\b"
        summary = re.sub(pattern_exact, lambda m, p=img["path"]: p, summary)
        
        # Second, fallback for when Mistral hallucinates literal strings like `![Figure 1: X](path)`
        fig_match = re.search(r'(?:Figure|Fig\.?)\s+(\d+)', img["context"], re.IGNORECASE)
        num_str = fig_match.group(1) if fig_match else str(img['index'] + 1)
        
        def replace_hallucinated_path(match, p=img["path"]):
            prefix, url = match.group(1), match.group(2)
            # If literal `path` or `image_path` or it lacks any directory structure, replace it
            if url.lower() in ["path", "image_path", "figure", "image"] or ("/" not in url and "\\" not in url):
                return f"{prefix}({p})"
            return match.group(0)
            
        pattern_fallback = r'(!\[(?:Figure|Fig\.?|Image)\s*' + num_str + r'[^\]]*\])\(([^)]+)\)'
        summary = re.sub(pattern_fallback, replace_hallucinated_path, summary, flags=re.IGNORECASE)

    return summary


def _strip_markdown_fences(text: str) -> str:
    """Strip wrapping ```markdown ... ``` fences if present."""
    if text.startswith("```markdown"):
        text = text[11:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


async def summarize_paper(text: str) -> str:
    """Send paper text to Bedrock Mistral and return a wiki-style markdown summary."""

    settings = get_settings()

    # Extract image info from the parsed markdown
    images = _extract_image_info(text)
    logger.info("Found %d images in the paper text", len(images))
    image_list_text = _build_image_list_text(images)

    user_message = f"Summarize the following research paper into a wiki-style markdown page:\n\n{text}"
    if image_list_text:
        user_message += image_list_text

    model_id = settings.MISTRAL_MODEL
    logger.info("Sending paper (%d chars) to Bedrock model %s", len(user_message), model_id)

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
            {"text": SYSTEM_PROMPT}
        ],
        inferenceConfig={
            "temperature": 0.3,
            "maxTokens": 8192,
        },
    )

    markdown_content = response["output"]["message"]["content"][0]["text"]
    markdown_content = _strip_markdown_fences(markdown_content)

    logger.info("Received markdown response (%d chars)", len(markdown_content))

    # Replace image placeholders with real paths
    if images:
        markdown_content = post_process_images(markdown_content, images)
        logger.info("Replaced image placeholders with real paths")

    return markdown_content
