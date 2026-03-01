import difflib
import logging
import os
import re
import shutil
import tempfile
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks

from app.schemas.paper import SummarizeRequest, SummarizeResponse, PipelineResponse
from app.services import mistral_service, s3_service
from app.services.wiki_parser import parse_pdf_to_markdown
from app.services.wiki_generator import generate_wiki_html
from app.config import get_settings
from app import database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers", tags=["Papers"])

# Resolve asset directories
_ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
_PAGES_DIR = os.path.join(_ASSETS_DIR, "pages")
_MD_DIR = os.path.join(_ASSETS_DIR, "markdowns")

def _upload_background_images(images_dir: str, s3_images_prefix: str, filenames: list[str]):
    """Background task to upload unused images to S3 so we don't block the API response."""
    for fname in filenames:
        fpath = os.path.join(images_dir, fname)
        if os.path.isfile(fpath):
            ct = "image/png" if fname.endswith(".png") else "image/jpeg" if fname.endswith((".jpg", ".jpeg")) else None
            try:
                s3_service.upload_file(fpath, f"{s3_images_prefix}/{fname}", content_type=ct, public=True)
            except Exception as e:
                logger.error("Failed to background upload %s: %s", fname, e)


def _normalize_name(name: str) -> str:
    """Normalize a filename for fuzzy comparison — strip extension, lowercase, remove non-alphanumeric."""
    name = os.path.splitext(name)[0]
    name = name.lower()
    name = re.sub(r'[\s\-_]+', '', name)
    name = re.sub(r'[^a-z0-9]', '', name)
    return name


def _find_existing_paper(filename: str, threshold: float = 0.8) -> str | None:
    """Return the ID of an already-processed paper whose filename closely matches filename."""
    normalized_new = _normalize_name(filename)
    if not normalized_new:
        return None
    try:
        rows = database.get_all_filenames()
    except Exception:
        return None
    best_ratio = 0.0
    best_id = None
    for paper_id, existing_filename in rows:
        normalized_existing = _normalize_name(existing_filename or "")
        if not normalized_existing:
            continue
        ratio = difflib.SequenceMatcher(None, normalized_new, normalized_existing).ratio()
        logger.debug("Fuzzy match '%s' vs '%s': ratio=%.4f", normalized_new, normalized_existing, ratio)
        if ratio > best_ratio:
            best_ratio = ratio
            best_id = paper_id
    logger.debug("Best fuzzy match for '%s': ratio=%.2f (id=%s)", filename, best_ratio, best_id)
    return best_id if best_ratio >= threshold else None


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
async def upload_paper(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Full pipeline: PDF → parse → summarize → HTML → S3 + DB."""

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # ── Deduplication check ─────────────────────────────────────────────
    existing_id = _find_existing_paper(file.filename)
    if existing_id:
        paper = database.get_paper_by_id(existing_id)
        # Extra safety: confirm the matched paper's filename is actually close to the upload
        if paper:
            stored_name = _normalize_name(paper.get("original_filename") or "")
            upload_name = _normalize_name(file.filename)
            match_ratio = difflib.SequenceMatcher(None, upload_name, stored_name).ratio()
            if match_ratio < 0.8:
                logger.warning(
                    "Dedup id=%s matched but ratio=%.2f is too low for '%s' vs '%s' — skipping cache",
                    existing_id, match_ratio, file.filename, paper.get("original_filename"),
                )
                paper = None  # force re-processing
        if paper:
            name = os.path.splitext(os.path.basename(paper.get("original_filename", "")))[0]
            if paper.get("s3_html_key"):
                html_url = s3_service.get_url(paper["s3_html_key"])
                md_url = s3_service.get_url(paper["s3_markdown_key"]) if paper.get("s3_markdown_key") else ""
            else:
                encoded_name = quote(name, safe="/-_.")
                html_url = f"/static/pages/{encoded_name}.html"
                md_url = f"/static/markdowns/{encoded_name}.md"
            md_path = os.path.join(_MD_DIR, f"{name}.md")
            markdown = ""
            if os.path.exists(md_path):
                with open(md_path, "r", encoding="utf-8") as f:
                    markdown = f.read()
            logger.info("Paper '%s' already exists (id=%s), returning cached result", file.filename, existing_id)
            return PipelineResponse(
                id=paper["id"],
                title=paper["title"],
                markdown=markdown,
                html_url=html_url,
                markdown_url=md_url,
                images_used=paper.get("images_used", 0),
                images_extracted=paper.get("images_extracted", 0),
                created_at=paper["created_at"],
            )

    try:
        pdf_bytes = await file.read()
        # Use only the basename (strip any OS path prefix some browsers may include)
        base_name = os.path.splitext(os.path.basename(file.filename))[0]

        # 1. Save PDF to temp using the original base_name so pymupdf4llm names
        #    extracted images as "{base_name}-{page}-{idx}.png" instead of random tmp names
        tmp_dir = tempfile.mkdtemp()
        tmp_pdf_path = os.path.join(tmp_dir, f"{base_name}.pdf")
        with open(tmp_pdf_path, "wb") as tmp_f:
            tmp_f.write(pdf_bytes)

        # 2. Parse PDF → text + images
        images_dir = os.path.join(_PAGES_DIR, f"{base_name}_images")
        os.makedirs(images_dir, exist_ok=True)
        raw_md = parse_pdf_to_markdown(tmp_pdf_path, images_dir)

        image_files = [f for f in os.listdir(images_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]

        # 3. Mistral summarization
        summary_md = await mistral_service.summarize_paper(raw_md)
        title = _extract_title(summary_md)
        img_refs = re.findall(r'!\[[^\]]*\]\([^)]+\)', summary_md)

        # 5. Rewrite image paths to browser-accessible /static/ URLs
        # The parser stores absolute paths like /app/app/assets/pages/NAME_images/img.png
        # We need them to be /static/pages/NAME_images/img.png
        images_rel = f"{base_name}_images"
        summary_for_html = re.sub(
            r'!\[([^\]]*)\]\([^)]*?' + re.escape(images_rel) + r'/([^)]+)\)',
            rf'![\1](/static/pages/{images_rel}/\2)',
            summary_md,
        )

        # 4. Save markdown locally (use rewritten /static/ paths so frontend can load images)
        os.makedirs(_MD_DIR, exist_ok=True)
        md_path = os.path.join(_MD_DIR, f"{base_name}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(summary_for_html)

        # 6. Generate HTML
        os.makedirs(_PAGES_DIR, exist_ok=True)
        html_content = generate_wiki_html(summary_for_html, base_name, _PAGES_DIR)
        html_path = os.path.join(_PAGES_DIR, f"{base_name}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # 6. Upload to S3 (optional — falls back to local)
        s3_pdf_key = ""
        s3_md_key = ""
        s3_html_key = ""
        s3_images_prefix = ""
        encoded_base = quote(base_name, safe="/-_.")
        html_url = f"/static/pages/{encoded_base}.html"
        md_url = f"/static/markdowns/{encoded_base}.md"
        # markdown to return — starts with /static/ paths, upgraded to S3 URLs if available
        final_markdown = summary_for_html

        settings = get_settings()
        if settings.S3_BUCKET_NAME and settings.AWS_ACCESS_KEY_ID:
            try:
                s3_prefix = f"papers/{base_name}"
                s3_pdf_key = s3_service.upload_bytes(pdf_bytes, f"{s3_prefix}/original.pdf", "application/pdf")
                s3_images_prefix = f"{s3_prefix}/images"
                
                # Separate used vs unused images to optimize upload speed
                used_filenames = [f for f in image_files if f in summary_md]
                unused_filenames = [f for f in image_files if f not in summary_md]
                
                # Upload used images synchronously
                for fname in used_filenames:
                    fpath = os.path.join(images_dir, fname)
                    ct = "image/png" if fname.endswith(".png") else "image/jpeg" if fname.endswith((".jpg", ".jpeg")) else None
                    s3_service.upload_file(fpath, f"{s3_images_prefix}/{fname}", content_type=ct, public=True)
                
                # Defer unused images to a background task
                background_tasks.add_task(_upload_background_images, images_dir, s3_images_prefix, unused_filenames)

                # Rewrite image URLs in markdown to point at S3
                s3_images_base = s3_service.get_url(s3_images_prefix)
                images_rel = f"{base_name}_images"
                final_markdown = re.sub(
                    r'!\[([^\]]*)\]\(/static/pages/' + re.escape(images_rel) + r'/([^)]+)\)',
                    rf'![\1]({s3_images_base}/\2)',
                    summary_for_html,
                )

                # Save S3-URL version to disk and upload
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(final_markdown)

                s3_md_key = s3_service.upload_file(md_path, f"{s3_prefix}/summary.md", "text/markdown")
                s3_html_key = s3_service.upload_file(html_path, f"{s3_prefix}/wiki.html", "text/html")
                html_url = s3_service.get_url(s3_html_key)
                md_url = s3_service.get_url(s3_md_key)
                logger.info("Uploaded to S3 successfully")
            except Exception as s3_err:
                logger.warning("S3 upload failed, using local files: %s", s3_err)

        # Clean up temp
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)

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
            markdown=final_markdown,
            html_url=html_url,
            markdown_url=md_url,
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
        for p in papers:
            if p.get("s3_html_key"):
                p["html_url"] = s3_service.get_url(p["s3_html_key"])
                p["markdown_url"] = s3_service.get_url(p["s3_markdown_key"]) if p.get("s3_markdown_key") else None
            else:
                # Fallback to local URLs
                name = os.path.splitext(os.path.basename(p.get("original_filename", "")))[0]
                encoded_name = quote(name, safe="/-_.")
                p["html_url"] = f"/static/pages/{encoded_name}.html"
                p["markdown_url"] = f"/static/markdowns/{encoded_name}.md"
        return papers
    except Exception as exc:
        logger.exception("Failed to list papers")
        raise HTTPException(status_code=500, detail=str(exc))


# ── GET /papers/{id} ────────────────────────────────────────────────────
@router.get("/{paper_id}")
async def get_paper(paper_id: str):
    """Get a single paper by ID, including its markdown content."""
    try:
        paper = database.get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        name = os.path.splitext(os.path.basename(paper.get("original_filename", "")))[0]

        if paper.get("s3_html_key"):
            paper["html_url"] = s3_service.get_url(paper["s3_html_key"])
            paper["markdown_url"] = s3_service.get_url(paper["s3_markdown_key"]) if paper.get("s3_markdown_key") else None
        else:
            encoded_name = quote(name, safe="/-_.")
            paper["html_url"] = f"/static/pages/{encoded_name}.html"
            paper["markdown_url"] = f"/static/markdowns/{encoded_name}.md"

        # Load markdown content from disk so frontend can render preview
        md_path = os.path.join(_MD_DIR, f"{name}.md")
        if os.path.exists(md_path):
            with open(md_path, "r", encoding="utf-8") as f:
                paper["markdown"] = f.read()
        else:
            paper["markdown"] = ""

        return paper
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get paper")
        raise HTTPException(status_code=500, detail=str(exc))

