import logging
import os
import re
import tempfile

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.schemas.paper import SummarizeRequest, SummarizeResponse, PipelineResponse
from app.services import mistral_service, s3_service
from app.services.wiki_parser import parse_pdf_to_markdown
from app.services.wiki_generator import generate_wiki_html
from app import database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers", tags=["Papers"])

# Resolve asset directories
_ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
_PAGES_DIR = os.path.join(_ASSETS_DIR, "pages")
_MD_DIR = os.path.join(_ASSETS_DIR, "markdowns")


def _extract_title(markdown: str) -> str:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return re.sub(r"^#+\s*", "", stripped)
    return "Untitled"


# ── POST /papers/summarize ──────────────────────────────────────────────
@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_paper(request: SummarizeRequest):
    """Accept raw paper text and return a wiki-style markdown summary."""
    try:
        markdown = await mistral_service.summarize_paper(request.text)
        title = _extract_title(markdown)
        return SummarizeResponse(title=title, markdown=markdown)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.exception("Summarization failed")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {exc}")


# ── POST /papers/upload ─────────────────────────────────────────────────
@router.post("/upload", response_model=PipelineResponse)
async def upload_paper(file: UploadFile = File(...)):
    """Full pipeline: PDF → parse → summarize → HTML → S3 + DB."""

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    try:
        pdf_bytes = await file.read()
        base_name = os.path.splitext(file.filename)[0]

        # 1. Save PDF to temp
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp.write(pdf_bytes)
        tmp.close()

        # 2. Parse PDF → text + images
        images_dir = os.path.join(_PAGES_DIR, f"{base_name}_images")
        os.makedirs(images_dir, exist_ok=True)
        raw_md = parse_pdf_to_markdown(tmp.name, images_dir)

        image_files = [f for f in os.listdir(images_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]

        # 3. Mistral summarization
        summary_md = await mistral_service.summarize_paper(raw_md)
        title = _extract_title(summary_md)
        img_refs = re.findall(r'!\[[^\]]*\]\([^)]+\)', summary_md)

        # 4. Save markdown locally
        os.makedirs(_MD_DIR, exist_ok=True)
        md_path = os.path.join(_MD_DIR, f"{base_name}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(summary_md)

        # 5. Generate HTML
        os.makedirs(_PAGES_DIR, exist_ok=True)
        html_content = generate_wiki_html(summary_md, base_name, _PAGES_DIR)
        html_path = os.path.join(_PAGES_DIR, f"{base_name}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # 6. Upload to S3
        s3_prefix = f"papers/{base_name}"
        s3_pdf_key = s3_service.upload_file(tmp.name if os.path.exists(tmp.name) else "", f"{s3_prefix}/original.pdf", "application/pdf") if os.path.exists(tmp.name) else ""

        # Upload PDF from bytes since temp may be deleted
        s3_pdf_key = s3_service.upload_bytes(pdf_bytes, f"{s3_prefix}/original.pdf", "application/pdf")
        s3_md_key = s3_service.upload_file(md_path, f"{s3_prefix}/summary.md", "text/markdown")
        s3_html_key = s3_service.upload_file(html_path, f"{s3_prefix}/wiki.html", "text/html")
        s3_images_prefix = f"{s3_prefix}/images"
        s3_service.upload_directory(images_dir, s3_images_prefix)

        # Clean up temp
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)

        # 7. Save to database
        paper_id, created_at = database.insert_paper(
            title=title,
            original_filename=file.filename,
            s3_pdf_key=s3_pdf_key,
            s3_markdown_key=s3_md_key,
            s3_html_key=s3_html_key,
            s3_images_prefix=s3_images_prefix,
            images_extracted=len(image_files),
            images_used=len(img_refs),
        )

        return PipelineResponse(
            id=paper_id,
            title=title,
            markdown=summary_md,
            html_url=s3_service.get_url(s3_html_key),
            markdown_url=s3_service.get_url(s3_md_key),
            images_used=len(img_refs),
            images_extracted=len(image_files),
            created_at=created_at,
        )

    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.exception("Upload pipeline failed")
        raise HTTPException(status_code=500, detail=f"Upload pipeline failed: {exc}")


# ── GET /papers ─────────────────────────────────────────────────────────
@router.get("/")
async def list_papers():
    """List all processed papers."""
    try:
        papers = database.get_all_papers()
        # Add S3 URLs
        for p in papers:
            p["html_url"] = s3_service.get_url(p["s3_html_key"]) if p.get("s3_html_key") else None
            p["markdown_url"] = s3_service.get_url(p["s3_markdown_key"]) if p.get("s3_markdown_key") else None
        return papers
    except Exception as exc:
        logger.exception("Failed to list papers")
        raise HTTPException(status_code=500, detail=str(exc))


# ── GET /papers/{id} ────────────────────────────────────────────────────
@router.get("/{paper_id}")
async def get_paper(paper_id: str):
    """Get a single paper by ID."""
    try:
        paper = database.get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        paper["html_url"] = s3_service.get_url(paper["s3_html_key"]) if paper.get("s3_html_key") else None
        paper["markdown_url"] = s3_service.get_url(paper["s3_markdown_key"]) if paper.get("s3_markdown_key") else None
        return paper
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get paper")
        raise HTTPException(status_code=500, detail=str(exc))
