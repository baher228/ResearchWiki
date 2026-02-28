import logging
import re
import asyncio

from mistralai import Mistral

from app.config import get_settings

from app.prompt import SYSTEM_PROMPT, SECTION_SYSTEM_PROMPT

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
        fig_placeholder = f"FIGURE_{img['index']}"
        
        # Try to find the true figure number from context to make the in-text replacement nice
        fig_match = re.search(r'(?:Figure|Fig\.?)\s+(\d+)', img["context"], re.IGNORECASE)
        fig_number = fig_match.group(1) if fig_match else str(img['index'] + 1)
        
        # Pass 1: Replace placeholder ONLY when it's inside a markdown image link: ![alt](FIGURE_N)
        # We look for the closing bracket and opening parenthesis `](` immediately preceding the placeholder.
        # Ensure we only match the exact placeholder by checking word boundary `\b` or `\)`
        img_pattern = rf"\]\({fig_placeholder}(?!\d)\)"
        summary = re.sub(img_pattern, f"]({img['path']})", summary)
        
        # Pass 2: Replace any remaining standalone instances with "Figure N"
        text_pattern = rf"\b{fig_placeholder}\b"
        summary = re.sub(text_pattern, f"Figure {fig_number}", summary)
        
    return summary

async def summarize_section(client: Mistral, chunk: str, image_list_text: str, settings, sem: asyncio.Semaphore) -> str:
    """Send a single section chunk to Mistral for summarization with concurrency limits."""
    async with sem:
        user_message = f"Summarize the following section of a research paper into wiki-style markdown:\n\n{chunk}"
        if image_list_text:
            user_message += image_list_text

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await client.chat.complete_async(
                    model=settings.MISTRAL_MODEL,
                    messages=[
                        {"role": "system", "content": SECTION_SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0.3,
                )
                break # Success!
            except Exception as e:
                import time
                if "429" in str(e) or "capacity exceeded" in str(e):
                    if attempt < max_retries - 1:
                        backoff = 2 ** attempt
                        logger.warning(f"Rate limited (429). Retrying in {backoff} seconds...")
                        await asyncio.sleep(backoff)
                        continue
                logger.error(f"Error summarizing section: {e}")
                # If rate limited permanently or other error, just return the original chunk as fallback
                return chunk

    markdown_content = response.choices[0].message.content
    
    # Strip fences
    if markdown_content.startswith("```markdown"):
        markdown_content = markdown_content[11:]
    elif markdown_content.startswith("```"):
        markdown_content = markdown_content[3:]
    if markdown_content.endswith("```"):
        markdown_content = markdown_content[:-3]
        
    return markdown_content.strip()

async def summarize_paper(text: str) -> str:
    """Send paper text to Mistral and return a wiki-style markdown summary with image references."""

    settings = get_settings()

    if not settings.MISTRAL_API_KEY or settings.MISTRAL_API_KEY == "your_mistral_api_key_here":
        raise ValueError(
            "MISTRAL_API_KEY is not configured. "
            "Please set a valid key in your .env file."
        )

    # Extract image info from the parsed markdown for global regex replacements later
    images = _extract_image_info(text)
    logger.info("Found %d images in the paper text", len(images))

    client = Mistral(api_key=settings.MISTRAL_API_KEY)

    # Split text into sections by H2 headers "## "
    chunks = re.split(r'\n(?=##\s)', text)
    chunks = [c.strip() for c in chunks if c.strip()]
    logger.info("Split paper into %d sections for parallel processing", len(chunks))

    # Process all sections concurrently with a limit of 2 at a time
    sem = asyncio.Semaphore(2)
    async def _pass_through(text: str) -> str:
        return text

    tasks = []
    for chunk in chunks:
        if re.match(r'^##\s+(references|bibliography)', chunk, re.IGNORECASE):
            tasks.append(_pass_through(chunk))
            logger.info("Keeping References section verbatim")
        else:
            # Extract images ONLY for this specific chunk so the AI doesn't hallucinate
            # pulling global images from other sections into this one.
            chunk_images = _extract_image_info(chunk)
            chunk_image_list_text = _build_image_list_text(chunk_images)
            tasks.append(summarize_section(client, chunk, chunk_image_list_text, settings, sem))
            
    summaries = await asyncio.gather(*tasks)

    # Combine back into a single document
    markdown_content = "\n\n".join(summaries)
    logger.info("Received and merged markdown responses (%d chars)", len(markdown_content))

    # Replace image placeholders with real paths
    if images:
        markdown_content = post_process_images(markdown_content, images)
        logger.info("Replaced image placeholders with real paths")

    return markdown_content
