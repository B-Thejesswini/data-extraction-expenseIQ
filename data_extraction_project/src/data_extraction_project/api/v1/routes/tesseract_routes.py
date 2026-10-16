from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.concurrency import run_in_threadpool

from data_extraction_project.api.v1.deps import get_tesseract_service
from data_extraction_project.schemas.ocr_schema import TesseractResponse
from data_extraction_project.services.tesseract_service import TesseractService

router = APIRouter(prefix="/ocr", tags=["ocr"])


@router.post("/tesseract", response_model=TesseractResponse)
async def tesseract_extract(
    file: UploadFile = File(...),
    service: TesseractService = Depends(get_tesseract_service),
) -> TesseractResponse:
    """ extract content from an image through tesseract
    
    returns the extracted content + confidence
    """
    content = await file.read()
    return await run_in_threadpool(service.extract, file.filename or "upload", content)