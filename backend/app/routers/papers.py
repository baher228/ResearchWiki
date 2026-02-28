import logging
import os
import re
import tempfile

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.schemas.paper import SummarizeRequest, SummarizeResponse, PipelineResponse
from app.services import mistral_service
from app.services.wiki_parser import parse_pdf_to_markdown
from app.services.wiki_generator import generate_wiki_html

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers", tags=["Papers"])

# Resolve asset directories once
_ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
_PAGES_DIR = os.path.join(_ASSETS_DIR, "pages")
_MD_DIR = os.path.join(_ASSETS_DIR, "markdowns")


def _extract_title(markdown: str) -> str:
    """Pull the first heading from the markdown as the paper title."""
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return re.sub(r"^#+\s*", "", stripped)
    return "Untitled"

@router.post("/upload", response_model=PipelineResponse)
async def upload_paper(file: UploadFile = File(...)):

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    try:
        pdf_bytes = await file.read()
        base_name = os.path.splitext(file.filename)[0]

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp.write(pdf_bytes)
        tmp.close()
        logger.info("Saved uploaded PDF (%d bytes) to %s", len(pdf_bytes), tmp.name)

        # ── 2. Parse PDF → text + images ────────────────────────────────
        images_dir = os.path.join(_PAGES_DIR, f"{base_name}_images")
        os.makedirs(images_dir, exist_ok=True)

        raw_md = parse_pdf_to_markdown(tmp.name, images_dir)
        logger.info("Parsed PDF: %d chars, images dir: %s", len(raw_md), images_dir)

        # Clean up temp file
        os.unlink(tmp.name)

        # Count extracted images
        image_files = [
            f for f in os.listdir(images_dir)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ]

        # ── 3. Mistral summarization (image-aware) ──────────────────────
        summary_md = await mistral_service.summarize_paper(raw_md)
        title = _extract_title(summary_md)

        # Count images referenced in the summary
        img_refs = re.findall(r'!\[[^\]]*\]\([^)]+\)', summary_md)

        # ── 4. Save summary markdown ────────────────────────────────────
        os.makedirs(_MD_DIR, exist_ok=True)
        md_filename = f"{base_name}.md"
        md_path = os.path.join(_MD_DIR, md_filename)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(summary_md)
        logger.info("Saved summary markdown: %s", md_path)

        # ── 5. Generate wiki HTML ───────────────────────────────────────
        os.makedirs(_PAGES_DIR, exist_ok=True)
        html_content = generate_wiki_html(summary_md, base_name, _PAGES_DIR)
        html_filename = f"{base_name}.html"
        html_path = os.path.join(_PAGES_DIR, html_filename)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info("Generated wiki HTML: %s", html_path)

        # ── 6. Return response ──────────────────────────────────────────
        return PipelineResponse(
            title=title,
            markdown=summary_md,
            html_url=f"/static/pages/{html_filename}",
            markdown_url=f"/static/markdowns/{md_filename}",
            images_used=len(img_refs),
            images_extracted=len(image_files),
        )

    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.exception("Upload pipeline failed")
        raise HTTPException(status_code=500, detail=f"Upload pipeline failed: {exc}")
