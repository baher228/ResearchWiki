import difflib
import hashlib
import logging
import os
import re
import shutil
import tempfile
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Query

from app.schemas.paper import SummarizeRequest, SummarizeResponse, PipelineResponse
from app.services import mistral_service, s3_service, paper_linker
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

def _normalize_name(name: str) -> str:
    """Normalize a filename for fuzzy comparison — strip extension, lowercase, remove non-alphanumeric."""
    name = os.path.splitext(name)[0]
    name = name.lower()
    name = re.sub(r'[\s\-_]+', '', name)
    name = re.sub(r'[^a-z0-9]', '', name)
    return name


def _extract_title(markdown: str) -> str:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return re.sub(r"^#+\s*", "", stripped)
    return "Untitled"


def _remove_local_paper_artifacts(original_filename: str):
    """Delete local markdown/html/image artifacts for one paper filename."""
    base_name = os.path.splitext(os.path.basename(original_filename or ""))[0]
    if not base_name:
        return

    md_path = os.path.join(_MD_DIR, f"{base_name}.md")
    html_path = os.path.join(_PAGES_DIR, f"{base_name}.html")
    images_dir = os.path.join(_PAGES_DIR, f"{base_name}_images")

    for fpath in (md_path, html_path):
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
            except Exception as file_err:
                logger.warning("Failed deleting artifact '%s': %s", fpath, file_err)

    if os.path.isdir(images_dir):
        try:
            shutil.rmtree(images_dir, ignore_errors=True)
        except Exception as dir_err:
            logger.warning("Failed deleting image directory '%s': %s", images_dir, dir_err)


def _paper_public_urls(paper: dict) -> tuple[str, str]:
    """Build public HTML/markdown URLs for a stored paper row."""
    orig_filename = paper.get("original_filename") or ""
    name = os.path.splitext(os.path.basename(orig_filename))[0]
    if paper.get("s3_html_key"):
        html_url = s3_service.get_url(paper["s3_html_key"])
        md_url = s3_service.get_url(paper["s3_markdown_key"]) if paper.get("s3_markdown_key") else ""
    else:
        encoded_name = quote(name, safe="/-_.")
        html_url = f"/static/pages/{encoded_name}.html"
        md_url = ""
    return html_url, md_url


def _dedupe_related_items(items: list[dict], limit: int) -> list[dict]:
    """Deduplicate related-paper rows by normalized title; keep highest score."""
    best_by_title: dict[str, dict] = {}

    for item in items:
        key = _normalize_name(item.get("title") or "") or (item.get("id") or "")
        if not key:
            continue

        existing = best_by_title.get(key)
        current_score = float(item.get("score") or 0)
        existing_score = float(existing.get("score") or 0) if existing else -1

        if not existing or current_score > existing_score:
            best_by_title[key] = item

    deduped = list(best_by_title.values())
    deduped.sort(key=lambda row: float(row.get("score") or 0), reverse=True)
    return deduped[:limit]


def _hydrate_related_papers(paper_id: str, limit: int = 5) -> list[dict]:
    """Return related papers with URLs for UI/API consumption."""
    fetch_limit = min(200, max(limit * 5, limit))
    related = database.get_related_papers(paper_id, limit=fetch_limit)
    for item in related:
        html_url, md_url = _paper_public_urls(item)
        item["html_url"] = html_url
        item["markdown_url"] = md_url
    return _dedupe_related_items(related, limit)


def _load_cached_markdown_for_paper(paper: dict) -> str:
    """Load cached summary markdown from S3 via stored key."""
    s3_md_key = paper.get("s3_markdown_key")
    if not s3_md_key:
        return ""

    try:
        return s3_service.get_text(s3_md_key)
    except Exception as exc:
        logger.warning("Failed to read markdown from S3 for id=%s: %s", paper.get("id"), exc)
        return ""


def _compute_and_store_links_for_paper(source_paper: dict, max_results: int = 5) -> list[dict]:
    """Compute and persist linkage edges for one source paper."""
    source_id = source_paper["id"]
    source_title = source_paper.get("title") or "Untitled"
    source_markdown = _load_cached_markdown_for_paper(source_paper)

    all_papers = database.get_all_papers()
    candidates = [paper for paper in all_papers if paper.get("id") != source_id]
    related_papers = paper_linker.find_related_papers(
        source_title=source_title,
        source_markdown=source_markdown,
        candidates=candidates,
        max_results=max_results,
        min_score=0.22,
    )

    database.insert_paper_links(source_id, related_papers)
    for link in related_papers:
        database.upsert_paper_link(
            source_paper_id=link["id"],
            target_paper_id=source_id,
            relation_type=link.get("relation_type") or "related_topic",
            score=float(link.get("score") or 0),
            evidence=link.get("evidence") or "",
        )

    for item in related_papers:
        target_row = next((paper for paper in candidates if paper.get("id") == item["id"]), None)
        if target_row:
            html_u, md_u = _paper_public_urls(target_row)
            item["html_url"] = html_u
            item["markdown_url"] = md_u

    return related_papers


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

    try:
        pdf_bytes = await file.read()
        content_hash = hashlib.sha256(pdf_bytes).hexdigest()

        # ── Deduplication check (content hash only) ──
        existing_id = database.get_paper_id_by_content_hash(content_hash)

        if existing_id:
            paper = database.get_paper_by_id(existing_id)
            if paper:
                html_url, md_url = _paper_public_urls(paper)
                markdown = _load_cached_markdown_for_paper(paper)

                if not markdown:
                    logger.info(
                        "Skipping cache for '%s' because DB markdown is empty",
                        file.filename,
                    )
                    paper = None

            if paper:
                related_papers = _hydrate_related_papers(paper["id"], limit=5)
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
                    related_papers=related_papers,
                )

        # Use only the basename (strip any OS path prefix some browsers may include)
        base_name = os.path.splitext(os.path.basename(file.filename))[0]

        # 1. Save PDF to temp using the original base_name so pymupdf4llm names
        #    extracted images as "{base_name}-{page}-{idx}.png" instead of random tmp names
        tmp_dir = tempfile.mkdtemp()
        tmp_pdf_path = os.path.join(tmp_dir, f"{base_name}.pdf")
        with open(tmp_pdf_path, "wb") as tmp_f:
            tmp_f.write(pdf_bytes)

        # 2. Parse PDF → text + images (temporary only)
        images_dir = os.path.join(tmp_dir, f"{base_name}_images")
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

        # 6. Generate HTML (in-memory)
        html_content = generate_wiki_html(summary_for_html, base_name, _PAGES_DIR)

        # 7. Upload to S3 (required)
        s3_pdf_key = ""
        s3_md_key = ""
        s3_html_key = ""
        s3_images_prefix = ""
        html_url = ""
        md_url = ""
        # markdown to return — starts with /static/ paths, upgraded to S3 URLs if available
        final_markdown = summary_for_html

        settings = get_settings()
        if not (settings.S3_BUCKET_NAME and settings.AWS_ACCESS_KEY_ID):
            raise HTTPException(status_code=503, detail="S3 configuration is required for paper storage.")

        try:
            s3_prefix = f"papers/{base_name}"
            s3_pdf_key = s3_service.upload_bytes(pdf_bytes, f"{s3_prefix}/original.pdf", "application/pdf", public=True)
            s3_images_prefix = f"{s3_prefix}/images"

            # Upload extracted images from temporary directory
            for fname in image_files:
                fpath = os.path.join(images_dir, fname)
                ct = "image/png" if fname.endswith(".png") else "image/jpeg" if fname.endswith((".jpg", ".jpeg")) else None
                s3_service.upload_file(fpath, f"{s3_images_prefix}/{fname}", content_type=ct, public=True)

            # Rewrite image URLs in markdown to point at S3
            s3_images_base = s3_service.get_url(s3_images_prefix)
            images_rel = f"{base_name}_images"
            final_markdown = re.sub(
                r'!\[([^\]]*)\]\(/static/pages/' + re.escape(images_rel) + r'/([^)]+)\)',
                rf'![\1]({s3_images_base}/\2)',
                summary_for_html,
            )

            s3_md_key = s3_service.upload_bytes(final_markdown.encode("utf-8"), f"{s3_prefix}/summary.md", "text/markdown", public=True)
            s3_html_key = s3_service.upload_bytes(html_content.encode("utf-8"), f"{s3_prefix}/wiki.html", "text/html", public=True)
            html_url = s3_service.get_url(s3_html_key)
            md_url = s3_service.get_url(s3_md_key)
            logger.info("Uploaded to S3 successfully")
        except HTTPException:
            raise
        except Exception as s3_err:
            logger.exception("S3 upload failed")
            raise HTTPException(status_code=503, detail=f"S3 upload failed: {s3_err}")

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
            content_hash=content_hash,
            markdown="",
        )

        # 8. Build and persist related-paper links (new -> existing and reverse)
        related_papers = []
        try:
            source_row = {
                "id": paper_id,
                "title": title,
                "original_filename": file.filename,
            }
            related_papers = _compute_and_store_links_for_paper(source_row, max_results=5)
        except Exception as link_err:
            logger.warning("Related-paper linkage generation failed for %s: %s", paper_id, link_err)
            related_papers = []

        return PipelineResponse(
            id=paper_id,
            title=title,
            markdown=final_markdown,
            html_url=html_url,
            markdown_url=md_url,
            images_used=len(img_refs),
            images_extracted=len(image_files),
            created_at=created_at,
            related_papers=related_papers,
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
            p["html_url"], p["markdown_url"] = _paper_public_urls(p)
        return papers
    except Exception as exc:
        logger.exception("Failed to list papers")
        raise HTTPException(status_code=500, detail=str(exc))


# ── DELETE /papers ──────────────────────────────────────────────────────
@router.delete("/")
async def clean_database():
    """Clear all papers and links from the database."""
    try:
        deleted_count = database.delete_all_papers()
        return {"deleted": deleted_count, "message": f"Successfully deleted {deleted_count} papers from the database."}
    except Exception as exc:
        logger.exception("Failed to clean database")
        raise HTTPException(status_code=500, detail=str(exc))


# ── GET /papers/{id} ────────────────────────────────────────────────────
@router.get("/{paper_id}")
async def get_paper(paper_id: str):
    """Get a single paper by ID, including its markdown content."""
    try:
        paper = database.get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        paper["html_url"], paper["markdown_url"] = _paper_public_urls(paper)

        # Load markdown content from DB
        paper["markdown"] = _load_cached_markdown_for_paper(paper)

        paper["related_papers"] = _hydrate_related_papers(paper_id, limit=5)

        return paper
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get paper")
        raise HTTPException(status_code=500, detail=str(exc))


# ── GET /papers/{id}/links ─────────────────────────────────────────────
@router.get("/{paper_id}/links")
async def get_paper_links(paper_id: str, limit: int = Query(default=20, ge=1, le=100)):
    """Get related paper links for one paper."""
    try:
        paper = database.get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        return _hydrate_related_papers(paper_id, limit=limit)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get paper links")
        raise HTTPException(status_code=500, detail=str(exc))

