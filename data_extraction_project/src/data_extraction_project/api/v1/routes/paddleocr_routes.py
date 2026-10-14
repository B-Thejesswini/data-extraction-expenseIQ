from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.concurrency import run_in_threadpool

from data_extraction_project.api.v1.deps import get_ocr_service
from data_extraction_project.schemas.ocr_schema import OCRResponse
from data_extraction_project.services.paddleocr_service import PaddleOCRService

router = APIRouter(prefix="/ocr", tags=["ocr"])


@router.post("/paddleocr", response_model=OCRResponse)
async def paddleocr_extract(
    file: UploadFile = File(...),
    service: PaddleOCRService = Depends(get_ocr_service),
) -> OCRResponse:
    content = await file.read()
    return await run_in_threadpool(service.extract, file.filename or "upload", content)