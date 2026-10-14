from fastapi import APIRouter, Depends, File, UploadFile

from data_extraction_project.api.v1.deps import get_gemini_service
from data_extraction_project.schemas.vlm_extraction_schema import ExtractionResponse
from data_extraction_project.services.gemini_service import GeminiService

router = APIRouter(prefix="/extract", tags=["extraction"])


@router.post(
    "/gemini",
    response_model=ExtractionResponse,
)
async def gemini_extract(
    file: UploadFile = File(...),
    service: GeminiService = Depends(get_gemini_service),
) -> ExtractionResponse:
    content = await file.read()
    return await service.extract(file.filename or "upload", content)