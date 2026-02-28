import logging
import re

from mistralai import Mistral

from app.config import get_settings

from app.prompt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def _extract_image_info(paper_text: str) -> list[dict]:
    """Extract image paths and their surrounding context (figure captions) from the parsed markdown."""
    images = []
    lines = paper_text.split("\n")
    for i, line in enumerate(lines):
        match = re.search(r'!\[([^\]]*)\]\(([^)]+)\)', line)
        if match:
            alt_text = match.group(1)
            path = match.group(2)
            # Grab surrounding lines for context (caption is usually nearby)
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
        # Try to find a figure number from nearby context
        fig_match = re.search(r'(?:Figure|Fig\.?)\s+(\d+)', img["context"], re.IGNORECASE)
        fig_label = f"Figure {fig_match.group(1)}" if fig_match else f"Image {img['index'] + 1}"
        parts.append(f"- FIGURE_{img['index']}: {fig_label}")
        # Add a snippet of the caption context
        caption_lines = [l.strip() for l in img["context"].split("\n") if l.strip() and not l.strip().startswith("![")]
        if caption_lines:
            parts.append(f"  Context: {' '.join(caption_lines[:2])}")
    return "\n".join(parts)


def post_process_images(summary: str, images: list[dict]) -> str:
    """Replace FIGURE_N placeholders in the summary with actual image paths using word boundaries."""
    for img in images:
        # Use a regex word boundary to prevent FIGURE_1 replacing FIGURE_16
        pattern = r"\bFIGURE_" + str(img['index']) + r"\b"
        summary = re.sub(pattern, img["path"], summary)
    return summary


async def summarize_paper(text: str) -> str:
    """Send paper text to Mistral and return a wiki-style markdown summary with image references."""

    settings = get_settings()

    if not settings.MISTRAL_API_KEY or settings.MISTRAL_API_KEY == "your_mistral_api_key_here":
        raise ValueError(
            "MISTRAL_API_KEY is not configured. "
            "Please set a valid key in your .env file."
        )

    # Extract image info from the parsed markdown
    images = _extract_image_info(text)
    image_list_text = _build_image_list_text(images)
    logger.info("Found %d images in the paper text", len(images))

    client = Mistral(api_key=settings.MISTRAL_API_KEY)

    user_message = f"Summarize the following research paper into a wiki-style markdown page:\n\n{text}"
    if image_list_text:
        user_message += image_list_text

    logger.info("Sending paper (%d chars) to Mistral model %s", len(user_message), settings.MISTRAL_MODEL)

    response = await client.chat.complete_async(
        model=settings.MISTRAL_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
    )

    markdown_content = response.choices[0].message.content
    
    # Mistral sometimes wraps the response in a ```markdown ... ``` block. We need to strip it out.
    if markdown_content.startswith("```markdown"):
        markdown_content = markdown_content[11:]
    elif markdown_content.startswith("```"):
        markdown_content = markdown_content[3:]
    if markdown_content.endswith("```"):
        markdown_content = markdown_content[:-3]
        
    markdown_content = markdown_content.strip()

    logger.info("Received markdown response (%d chars)", len(markdown_content))

    # Replace image placeholders with real paths
    if images:
        markdown_content = post_process_images(markdown_content, images)
        logger.info("Replaced image placeholders with real paths")

    return markdown_content
