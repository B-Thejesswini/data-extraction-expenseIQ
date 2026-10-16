from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool

from data_extraction_project.api.v1.deps import get_pdf_to_markdown_service, uploaded_pdf
from data_extraction_project.schemas.markdown import MarkdownResponse
from data_extraction_project.services.pdf_markdown_service import PdfToMarkdownService

router = APIRouter(prefix="/extract", tags=["extraction"])


@router.post("/pdf-to-markdown", response_model=MarkdownResponse)
async def pdf_to_markdown(
    pdf_path: Path = Depends(uploaded_pdf),
    service: PdfToMarkdownService = Depends(get_pdf_to_markdown_service),
) -> MarkdownResponse:
    """ Uses pymupdf to parse a pdf into markdown
    """
    markdown = await run_in_threadpool(service.convert, pdf_path)
    return MarkdownResponse(markdown=markdown)