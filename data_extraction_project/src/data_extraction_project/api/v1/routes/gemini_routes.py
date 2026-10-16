from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile

from data_extraction_project.api.v1.deps import (
    get_gemini_service, 
    get_pdf_extraction_service,
    uploaded_pdf
)

from data_extraction_project.schemas.vlm_extraction_schema import ExtractionResponse
from data_extraction_project.services.gemini_service import GeminiService

from data_extraction_project.services.pdf_extraction_service import PdfExtractionService

router = APIRouter(prefix="/extract", tags=["extraction"])


@router.post(
    "/gemini-img",
    response_model=ExtractionResponse,
)
async def gemini_extract_from_img(
    file: UploadFile = File(...),
    service: GeminiService = Depends(get_gemini_service),
) -> ExtractionResponse:
    """ extract receipt data directly from an image via Gemini"""
    content = await file.read()
    return await service.extract(file.filename or "upload", content)


@router.post(
    "/gemini-markdown",
    response_model=ExtractionResponse,
)
async def gemini_markdown_extract(
    file: UploadFile = File(...),
    service: GeminiService = Depends(get_gemini_service),
) -> ExtractionResponse:
    """ extract receipt data from markdown via Gemini"""
    content = await file.read()
    return await service.extract_markdown(file.filename or "upload", content)

@router.post(
    "/gemini-pdf",
    response_model=ExtractionResponse,
)
async def gemini_pdf_extract(
    pdf_path: Path = Depends(uploaded_pdf),
    service: PdfExtractionService = Depends(get_pdf_extraction_service),
) -> ExtractionResponse:
    """ extract receipt data directly from a PDF via Gemini """
    return await service.extract(pdf_path)