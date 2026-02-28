import logging
import re

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.schemas.paper import SummarizeRequest, SummarizeResponse
from app.services import mistral_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers", tags=["Papers"])


def _extract_title(markdown: str) -> str:
    """Pull the first heading from the markdown as the paper title."""
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return re.sub(r"^#+\s*", "", stripped)
    return "Untitled"


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_paper(request: SummarizeRequest):
    """Accept research paper text and return a wiki-style markdown summary."""

    try:
        markdown = await mistral_service.summarize_paper(request.text)
        title = _extract_title(markdown)
        return SummarizeResponse(title=title, markdown=markdown)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.exception("Summarization failed")
        raise HTTPException(
            status_code=500,
            detail=f"Summarization failed: {exc}",
        )


@router.post("/upload")
async def upload_paper(file: UploadFile = File(...)):
    try:
        from app.services import pdf_parser
        content = await pdf_parser.parse_pdf(file)
        markdown = await mistral_service.summarize_paper(content)
        title = _extract_title(markdown)
        return SummarizeResponse(title=title, markdown=markdown)
    except Exception as exc:
        logger.exception("Upload failed")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {exc}",
        )
