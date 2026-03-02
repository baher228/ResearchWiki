import json
import logging
import re
import asyncio
from urllib import request, error

from app.config import get_settings
from app.prompt import PROMPT_1, PROMPT_2, PROMPT_3, PROMPT_4, PROMPT_5

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


def _mistral_chat_completion(*, model: str, system_prompt: str | None, user_message: str, temperature: float, max_tokens: int) -> str:
    settings = get_settings()
    if not settings.MISTRAL_API_KEY:
        raise RuntimeError("MISTRAL_API_KEY is not set")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": model,
        "messages": messages,
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
        parts.append(f"- FIGURE_{img['index'] + 1}: {fig_label}")
        caption_lines = [l.strip() for l in img["context"].split("\n") if l.strip() and not l.strip().startswith("![")]
        if caption_lines:
            parts.append(f"  Context: {' '.join(caption_lines[:2])}")
    return "\n".join(parts)


def post_process_images(summary: str, images: list[dict]) -> str:
    """Replace image placeholders in the summary with actual image paths."""
    for img in images:
        # First, safely replace exact FIGURE_N placeholders using lambda to avoid escape char bugs
        pattern_exact = r"\bFIGURE_" + str(img['index'] + 1) + r"\b"
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


async def summarize_paper(text: str, system_prompt: str = PROMPT_1) -> str:
    """Send paper text to Mistral API and return a wiki-style markdown summary."""

    settings = get_settings()

    # Extract image info from the parsed markdown
    images = _extract_image_info(text)
    logger.info("Found %d images in the paper text", len(images))
    image_list_text = _build_image_list_text(images)

    user_message = f"Summarize the following research paper into a wiki-style markdown page:\n\n{text}"
    if image_list_text:
        user_message += image_list_text

    model_id = settings.MISTRAL_MODEL
    logger.info("Sending paper (%d chars) to Mistral model %s", len(user_message), model_id)

    markdown_content = await asyncio.to_thread(
        _mistral_chat_completion,
        model=model_id,
        system_prompt=system_prompt,
        user_message=user_message,
        temperature=0.3,
        max_tokens=8192,
    )
    markdown_content = _strip_markdown_fences(markdown_content)

    logger.info("Received markdown response (%d chars)", len(markdown_content))

    # Replace image placeholders with real paths
    if images:
        markdown_content = post_process_images(markdown_content, images)
        logger.info("Replaced image placeholders with real paths")

    return markdown_content


async def generate_all_summaries(text: str) -> list[str]:
    """Generates 5 different complexity levels concurrently."""
    prompts = [PROMPT_1, PROMPT_2, PROMPT_3, PROMPT_4, PROMPT_5]
    # prompts = [PROMPT_1, PROMPT_3, PROMPT_5]
    
    logger.info("Starting concurrent generation of 5 summary levels")
    tasks = [summarize_paper(text, system_prompt=p) for p in prompts]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results, replacing errors with a fallback message
    processed_results = []
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            logger.error("Failed to generate summary level %d: %s", i + 1, res)
            processed_results.append(f"# Level {i + 1} Summary Failed\n\nAn error occurred generating this summary level.\n\n`{str(res)}`")
        else:
            processed_results.append(res)
            
    return processed_results


async def generate_linked_papers(source_title: str, source_markdown: str, candidates: list[dict], max_results: int = 5) -> list[dict]:
    """Ask Mistral to find topically related candidate papers."""
    settings = get_settings()

    if not candidates:
        return []

    # Create a concise representation of candidates to fit in context window
    candidates_text = ""
    for c in candidates:
        c_title = c.get("title") or "Untitled"
        c_md = c.get("markdown") or ""
        # take first 300 chars of markdown
        c_snippet = c_md[:300].replace('\n', ' ') + "..." if len(c_md) > 300 else c_md.replace('\n', ' ')
        candidates_text += f"- ID: {c['id']}\n  Title: {c_title}\n  Snippet: {c_snippet}\n\n"

    source_snippet = source_markdown[:2000]

    system_prompt = "You are an AI assistant that links research papers based on their topical similarity."
    user_prompt = f"""Given the following source paper:
Title: {source_title}
Snippet: {source_snippet}

And the following candidate papers:
{candidates_text}

Identify up to {max_results} candidate papers that are most topically related to the source paper. 
Return ONLY a JSON array of objects, where each object has:
- "id": the ID of the candidate paper (must exactly match one of the candidate IDs)
- "relation_type": either "extends_or_compares" or "related_topic"
- "score": a float between 0.0 and 1.0 representing the confidence of the link
- "evidence": a short 1-sentence explanation of why they are related.

Ensure the output is valid JSON."""

    model_id = settings.MISTRAL_MODEL
    output_text = await asyncio.to_thread(
        _mistral_chat_completion,
        model=model_id,
        system_prompt=system_prompt,
        user_message=user_prompt,
        temperature=0.1,
        max_tokens=2048,
    )
    try:
        if "```json" in output_text:
            output_text = output_text.split("```json")[1].split("```")[0].strip()
        elif "```" in output_text:
            output_text = output_text.split("```")[1].split("```")[0].strip()
        
        related_data = json.loads(output_text)
        if not isinstance(related_data, list):
            related_data = []
            
        # Filter out hallucinated IDs
        valid_ids = {c["id"] for c in candidates}
        related_data = [r for r in related_data if r.get("id") in valid_ids]
        
        # Sort by score and limit
        related_data.sort(key=lambda x: float(x.get("score", 0)), reverse=True)
        return related_data[:max_results]
    except Exception as e:
        logger.error("Failed to parse Mistral linked papers output: %s", e)
        return []

