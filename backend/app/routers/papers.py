import logging

from fastapi import APIRouter, HTTPException

from app.schemas.paper import SummarizeRequest, SummarizeResponse
from app.services import mistral_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers", tags=["Papers"])


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_paper(request: SummarizeRequest):
    """Accept research paper text and return a wiki-style summary."""

    try:
        result = await mistral_service.summarize_paper(request.text)
        return SummarizeResponse(**result)
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
        content = await pdf_parser.parse_pdf(file)
        result = await mistral_service.summarize_paper(content)
        return SummarizeResponse(**result)
    except Exception as exc:
        logger.exception("Upload failed")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {exc}",
        )
