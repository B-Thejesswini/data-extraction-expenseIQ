from fastapi import APIRouter, Depends, File, UploadFile

from data_extraction_project.api.v1.deps import get_groq_service
from data_extraction_project.schemas.vlm_extraction_schema import ExtractionResponse
from data_extraction_project.services.groq_service import GroqService

router = APIRouter(prefix="/extract", tags=["extraction"])


@router.post(
    "/groq",
    response_model=ExtractionResponse,
)
async def groq_extract(
    file: UploadFile = File(...),
    service: GroqService = Depends(get_groq_service),
) -> ExtractionResponse:
    """ extract receipt data directly from an image via Groq's qwen model"""
    content = await file.read()
    return await service.extract(file.filename or "upload", content)