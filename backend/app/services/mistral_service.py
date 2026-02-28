import logging
import re

from mistralai import Mistral

from app.config import get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert academic summarizer. Your job is to READ a research paper and produce a CONCISE, wiki-style Markdown summary — like a Wikipedia article about the paper.

IMPORTANT: You must SUMMARIZE and CONDENSE the paper, NOT reproduce it verbatim. A typical 15-page paper should become a 2-4 page wiki article. Distill the key ideas, methods, results, and contributions into accessible prose.

Format requirements:
1. Start with the paper title as an H4 heading (####), followed by the authors in bold with their affiliations on the next line.
2. Use H2 headings (##) for sections. Use this structure:
   - ## Abstract (2-3 sentence summary of the paper's purpose and findings)
   - ## Background (why this work matters, what problem it addresses)
   - ## Method (summarize the core approach — explain the key idea simply, include only the most important equations)
   - ## Experiments & Results (highlight the main findings, comparisons, and takeaways)
   - ## Conclusion (key contributions and impact)
   - ## References (include only the 5-10 most important cited works)
3. Use H3 (###) for sub-sections only when needed.

Writing guidelines:
- Write in clear, encyclopedic language accessible to someone with general ML/science knowledge.
- Explain technical concepts — don't just state them. A reader unfamiliar with the paper should understand the summary.
- Condense multiple paragraphs into key sentences. Cut redundancy, verbose explanations, and minor details.
- Use markdown formatting: **bold** for key terms, _italics_ for definitions, bullet lists for comparisons or enumerated contributions.

IMAGE GUIDELINES (very important):
- The paper text will contain image references in the format ![](image_path). These are figures extracted from the PDF.
- You will also receive a list of available image filenames.
- When a figure is important for understanding (e.g. architecture diagrams, key result plots, algorithm pseudocode), INCLUDE it in your summary using: ![Figure N: description](FIGURE_N)
- Use the placeholder FIGURE_N (e.g. FIGURE_1, FIGURE_2) and we will replace it with the actual image path later.
- Include 3-6 of the most important figures. Write a short caption for each.
- Place figures near the text that discusses them.
- Return ONLY the markdown content — no wrapping fences, no explanations, just the raw markdown document.
"""


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
    """Replace FIGURE_N placeholders in the summary with actual image paths."""
    for img in images:
        placeholder = f"FIGURE_{img['index']}"
        summary = summary.replace(placeholder, img["path"])
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
    logger.info("Received markdown response (%d chars)", len(markdown_content))

    # Replace image placeholders with real paths
    if images:
        markdown_content = post_process_images(markdown_content, images)
        logger.info("Replaced image placeholders with real paths")

    return markdown_content
