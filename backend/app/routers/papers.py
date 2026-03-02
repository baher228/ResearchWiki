import difflib
import hashlib
import logging
import os
import re
import shutil
import tempfile
import json
from urllib.parse import quote, unquote
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Query, Form, Request
from fastapi.responses import HTMLResponse, Response
from bs4 import BeautifulSoup

from app.schemas.paper import SummarizeRequest, SummarizeResponse, PipelineResponse
from app.services import mistral_service, s3_service, description_service
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


_GENERIC_TITLES = {
    "summary",
    "paper summary",
    "research paper summary",
    "overview",
    "introduction",
    "abstract",
    "untitled",
}


def _clean_title_candidate(text: str) -> str:
    text = re.sub(r"^#+\s*", "", text or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text.strip("-:| ")


def _is_generic_title(title: str) -> bool:
    t = (title or "").strip().lower()
    if not t:
        return True
    if t in _GENERIC_TITLES:
        return True
    if re.fullmatch(r"(section|part)\s+\d+", t):
        return True
    return False


def _title_from_filename(raw_name: str) -> str:
    candidate = re.sub(r"[_\-]+", " ", raw_name or "").strip()
    candidate = re.sub(r"\s+", " ", candidate)
    return candidate or "Untitled"


def _extract_title_from_raw_markdown(raw_md: str) -> str:
    """Best-effort title detection from parser output (before LLM rewriting)."""
    lines = raw_md.splitlines()
    for line in lines[:40]:
        s = _clean_title_candidate(line)
        if not s:
            continue
        if s.startswith("!") or s.startswith("["):
            continue
        if len(s) < 8 or len(s) > 220:
            continue
        lowered = s.lower()
        if lowered in {
            "abstract",
            "introduction",
            "references",
            "acknowledgments",
            "conclusion",
        }:
            continue
        if re.match(r"^\d+(\.\d+)*\s+", s):
            continue
        return s
    return ""


def _select_paper_title(summary_md: str, raw_md: str, raw_name: str) -> str:
    summary_title = _clean_title_candidate(_extract_title(summary_md or ""))
    if summary_title and not _is_generic_title(summary_title):
        return summary_title

    raw_title = _clean_title_candidate(_extract_title_from_raw_markdown(raw_md or ""))
    if raw_title and not _is_generic_title(raw_title):
        return raw_title

    return _title_from_filename(raw_name)


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
    orig_filename = str(paper.get("original_filename") or "")
    name = os.path.splitext(os.path.basename(orig_filename))[0]
    s3_html_key = paper.get("s3_html_key")
    s3_md_key = paper.get("s3_markdown_key")

    if isinstance(s3_html_key, str) and s3_html_key:
        try:
            html_url = s3_service.get_url(s3_html_key)
        except Exception as exc:
            logger.warning("Failed building HTML S3 URL for paper id=%s: %s", paper.get("id"), exc)
            html_url = ""

        if isinstance(s3_md_key, str) and s3_md_key:
            try:
                md_url = s3_service.get_url(s3_md_key)
            except Exception as exc:
                logger.warning("Failed building markdown S3 URL for paper id=%s: %s", paper.get("id"), exc)
                md_url = ""
        else:
            md_url = ""

        if html_url:
            return html_url, md_url

    if name:
        encoded_name = quote(name, safe="/-_.")
        html_url = f"/static/pages/{encoded_name}.html"
    else:
        html_url = ""
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


def _extract_summary_markdown_text(stored_markdown_blob: str) -> str:
    """Extract one markdown summary text from stored JSON/text payload."""
    text = (stored_markdown_blob or "").strip()
    if not text:
        return ""
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list) and parsed:
            first = parsed[0]
            return first if isinstance(first, str) else ""
        if isinstance(parsed, str):
            return parsed
    except Exception:
        pass
    return text


def _extract_summary_markdown_levels(stored_markdown_blob: str) -> list[str]:
    """Extract all markdown summary levels from stored JSON/text payload."""
    text = (stored_markdown_blob or "").strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, str) and item.strip()]
        if isinstance(parsed, str) and parsed.strip():
            return [parsed]
    except Exception:
        pass
    return [text]


def _rewrite_image_sources_for_backend(html_content: str, paper_id: str, paper: dict, base_url: str) -> str:
    """Rewrite image URLs in stored HTML so they are served via backend authenticated endpoint."""
    s3_images_prefix = str(paper.get("s3_images_prefix") or "")
    if not s3_images_prefix:
        return html_content

    prefix_token = f"/{s3_images_prefix}/"
    s3_prefix_token = f"{s3_images_prefix}/"

    soup = BeautifulSoup(html_content, "html.parser")
    changed = False

    for img in soup.find_all("img"):
        src = (img.get("src") or "").strip()
        if not src:
            continue

        image_name = ""
        if prefix_token in src:
            image_name = src.split(prefix_token, 1)[1]
        elif s3_prefix_token in src:
            image_name = src.split(s3_prefix_token, 1)[1]

        if not image_name:
            continue

        image_name = unquote(image_name).split("?", 1)[0].split("#", 1)[0].lstrip("/")
        if not image_name:
            continue

        img["src"] = f"{base_url}/papers/{paper_id}/image/{quote(image_name, safe='/')}"
        changed = True

    return str(soup) if changed else html_content




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


# ── POST /papers/description ──────────────────────────────────────────────
@router.post("/description", response_model=SummarizeResponse)
async def get_description(request: SummarizeRequest):
    """Accept raw paper text and return a wiki-style markdown summary."""
    try:
        description = await description_service.get_description(request.text)
        return SummarizeResponse(title="", markdown=description)
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
        refresh_existing_paper_id: Optional[str] = None

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
                    refresh_existing_paper_id = paper["id"]
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
        raw_name = os.path.splitext(os.path.basename(file.filename))[0]
        # Make the basename safe for filesystem and URLs
        base_name = re.sub(r'[\s]+', '_', raw_name)
        base_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '', base_name)

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

        # 3. Mistral summarization (concurrent mapping)
        summaries = await mistral_service.generate_all_summaries(raw_md)
        title = _select_paper_title(summaries[0], raw_md, raw_name)
        
        combined_md = "\n".join(summaries)
        img_refs = re.findall(r'!\[[^\]]*\]\([^)]+\)', combined_md)

        # 5. Rewrite image paths to browser-accessible /static/ URLs
        # The parser stores absolute paths like /app/app/assets/pages/NAME_images/img.png
        # We need them to be /static/pages/NAME_images/img.png
        images_rel = f"{base_name}_images"
        summaries_for_html = []
        for smd in summaries:
            s_html = re.sub(
                r'!\[([^\]]*)\]\([^)]*?' + re.escape(images_rel) + r'/([^)]+)\)',
                rf'![\1](/static/pages/{images_rel}/\2)',
                smd,
            )
            summaries_for_html.append(s_html)

        # 6. Upload to S3 (required)
        s3_pdf_key = ""
        s3_md_key = ""
        s3_html_key = ""
        s3_images_prefix = ""
        html_url = ""
        md_url = ""
        # markdown to return — starts with /static/ paths, upgraded to S3 URLs if available
        final_markdown = summaries_for_html[0]

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
            
            final_summaries = []
            for s_html in summaries_for_html:
                f_md = re.sub(
                    r'!\[([^\]]*)\]\(/static/pages/' + re.escape(images_rel) + r'/([^)]+)\)',
                    rf'![\1]({s3_images_base}/\2)',
                    s_html,
                )
                final_summaries.append(f_md)

            final_markdown = final_summaries[0]

            # Generate HTML from final markdowns so uploaded HTML references S3 image URLs
            html_content = generate_wiki_html(final_summaries, base_name, _PAGES_DIR)

            summaries_json = json.dumps(final_summaries)
            s3_md_key = s3_service.upload_bytes(summaries_json.encode("utf-8"), f"{s3_prefix}/summary.json", "application/json", public=True)
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
        if refresh_existing_paper_id:
            updated = database.refresh_paper_storage(
                paper_id=refresh_existing_paper_id,
                title=title,
                original_filename=file.filename,
                s3_pdf_key=s3_pdf_key,
                s3_markdown_key=s3_md_key,
                s3_html_key=s3_html_key,
                s3_images_prefix=s3_images_prefix,
                images_extracted=len(image_files),
                images_used=len(img_refs),
                content_hash=content_hash,
            )
            if not updated:
                raise HTTPException(status_code=500, detail="Failed to refresh existing paper metadata")

            refreshed = database.get_paper_by_id(refresh_existing_paper_id)
            if not refreshed:
                raise HTTPException(status_code=500, detail="Refreshed paper not found")

            paper_id = refresh_existing_paper_id
            created_at = refreshed["created_at"]
        else:
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

        # 8. Related papers generation is now asynchronous and triggered by the frontend
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
async def list_papers(q: Optional[str] = None):
    """List all processed papers."""
    try:
        papers = database.get_all_papers(q)
        for p in papers:
            try:
                p["html_url"], p["markdown_url"] = _paper_public_urls(p)
            except Exception as row_err:
                logger.warning("Failed to build URLs for paper id=%s: %s", p.get("id"), row_err)
                p["html_url"], p["markdown_url"] = "", ""
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


# ── POST /papers/repair-titles ─────────────────────────────────────────
@router.post("/repair-titles")
async def repair_titles(limit: int = Query(default=5000, ge=1, le=20000)):
    """One-time maintenance endpoint: repair generic paper titles in DB."""
    try:
        papers = database.get_all_papers()
        scanned = 0
        updated = 0
        skipped = 0

        for paper in papers[:limit]:
            scanned += 1
            current_title = _clean_title_candidate(str(paper.get("title") or ""))

            if current_title and not _is_generic_title(current_title):
                skipped += 1
                continue

            original_filename = str(paper.get("original_filename") or "")
            raw_name = os.path.splitext(os.path.basename(original_filename))[0]

            summary_blob = _load_cached_markdown_for_paper(paper)
            summary_md = _extract_summary_markdown_text(summary_blob)
            new_title = _select_paper_title(summary_md, "", raw_name)

            if not new_title or _is_generic_title(new_title):
                skipped += 1
                continue

            if database.update_paper_title(str(paper["id"]), new_title):
                updated += 1
            else:
                skipped += 1

        return {
            "ok": True,
            "scanned": scanned,
            "updated": updated,
            "skipped": skipped,
            "total_in_db": len(papers),
        }
    except Exception as exc:
        logger.exception("Failed to repair titles")
        raise HTTPException(status_code=500, detail=str(exc))


# ── POST /papers/rerender-html ─────────────────────────────────────────
@router.post("/rerender-html")
async def rerender_html(limit: int = Query(default=5000, ge=1, le=20000), paper_id: Optional[str] = None):
    """One-time maintenance endpoint: re-render wiki HTML from stored markdown summaries."""
    try:
        papers = [database.get_paper_by_id(paper_id)] if paper_id else database.get_all_papers()
        papers = [p for p in papers if p]

        scanned = 0
        updated = 0
        skipped = 0

        for paper in papers[:limit]:
            scanned += 1

            s3_md_key = paper.get("s3_markdown_key")
            s3_html_key = paper.get("s3_html_key")
            if not s3_md_key or not s3_html_key:
                skipped += 1
                continue

            try:
                markdown_blob = s3_service.get_text(s3_md_key)
                levels = _extract_summary_markdown_levels(markdown_blob)
                if not levels:
                    skipped += 1
                    continue

                original_filename = str(paper.get("original_filename") or "")
                raw_name = os.path.splitext(os.path.basename(original_filename))[0]
                base_name = re.sub(r'[\s]+', '_', raw_name)
                base_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '', base_name)
                if not base_name:
                    base_name = "paper"

                html_content = generate_wiki_html(levels, base_name, _PAGES_DIR)
                s3_service.upload_bytes(html_content.encode("utf-8"), s3_html_key, "text/html", public=True)
                updated += 1
            except Exception as one_err:
                logger.warning("Failed rerender for paper id=%s: %s", paper.get("id"), one_err)
                skipped += 1

        return {
            "ok": True,
            "scanned": scanned,
            "updated": updated,
            "skipped": skipped,
            "total_in_db": len(papers),
        }
    except Exception as exc:
        logger.exception("Failed to rerender HTML")
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


# ── GET /papers/{id}/html ───────────────────────────────────────────────
@router.get("/{paper_id}/html")
async def get_paper_html(paper_id: str, request: Request):
    """Get the raw HTML content for a paper's wiki page."""
    try:
        paper = database.get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        s3_html_key = paper.get("s3_html_key")
        if s3_html_key:
            html_content = s3_service.get_text(s3_html_key)
            base_url = str(request.base_url).rstrip("/")
            html_content = _rewrite_image_sources_for_backend(html_content, paper_id, paper, base_url)
            return HTMLResponse(content=html_content)
        
        # Fallback to local file if no S3 key is present
        orig_filename = paper.get("original_filename") or ""
        raw_name = os.path.splitext(os.path.basename(orig_filename))[0]
        safe_name = re.sub(r'[\s]+', '_', raw_name)
        safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '', safe_name)

        candidate_names = [raw_name]
        if safe_name and safe_name != raw_name:
            candidate_names.append(safe_name)

        for candidate in candidate_names:
            local_path = os.path.join(_PAGES_DIR, f"{candidate}.html")
            if os.path.exists(local_path):
                with open(local_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                    base_url = str(request.base_url).rstrip("/")
                    html_content = _rewrite_image_sources_for_backend(html_content, paper_id, paper, base_url)
                    return HTMLResponse(content=html_content)
        
        raise HTTPException(status_code=404, detail="HTML content not found")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get paper HTML")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{paper_id}/image/{image_name:path}")
async def get_paper_image(paper_id: str, image_name: str):
    """Serve paper images through backend using configured S3 credentials."""
    try:
        paper = database.get_paper_by_id(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        s3_images_prefix = paper.get("s3_images_prefix")
        if not s3_images_prefix:
            raise HTTPException(status_code=404, detail="Paper has no image storage")

        normalized_name = unquote(image_name).lstrip("/")
        if not normalized_name:
            raise HTTPException(status_code=404, detail="Image not found")

        s3_key = f"{s3_images_prefix}/{normalized_name}"
        data, content_type = s3_service.get_object_bytes(s3_key)
        return Response(content=data, media_type=content_type or "application/octet-stream")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to load paper image")
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


# ── POST /papers/{id}/generate-links ───────────────────────────────────
@router.post("/{paper_id}/generate-links")
async def generate_paper_links(paper_id: str):
    """Asynchronously generate related paper links using Mistral."""
    try:
        source_paper = database.get_paper_by_id(paper_id)
        if not source_paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        source_title = source_paper.get("title") or "Untitled"
        source_markdown = _load_cached_markdown_for_paper(source_paper)

        all_papers = database.get_all_papers()
        candidates = [p for p in all_papers if p.get("id") != paper_id]

        if not candidates:
            return []

        # Load candidate markdowns
        for c in candidates:
            c["markdown"] = _load_cached_markdown_for_paper(c)

        related = await mistral_service.generate_linked_papers(source_title, source_markdown, candidates, max_results=5)

        database.insert_paper_links(paper_id, related)
        for link in related:
            database.upsert_paper_link(
                source_paper_id=link["id"],
                target_paper_id=paper_id,
                relation_type=link.get("relation_type") or "related_topic",
                score=float(link.get("score") or 0),
                evidence=link.get("evidence") or "",
            )

        return _hydrate_related_papers(paper_id, limit=5)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to generate links")
        raise HTTPException(status_code=500, detail=str(exc))

