# dependencies

from functools import lru_cache

from data_extraction_project.llm.providers.gemini_client import GeminiClient
from data_extraction_project.core.config import settings
from data_extraction_project.services.gemini_service import GeminiService
from data_extraction_project.services.pdf_extraction_service import PdfExtractionService

from data_extraction_project.services.paddleocr_service import PaddleOCRService
from data_extraction_project.services.tesseract_service import TesseractService

from data_extraction_project.llm.providers.groq_client import GroqClient
from data_extraction_project.services.groq_service import GroqService

import re
import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path

from fastapi import File, UploadFile

from data_extraction_project.services.pdf_markdown_service import PdfToMarkdownService



@lru_cache
def get_ocr_service() -> PaddleOCRService:
    return PaddleOCRService()


@lru_cache
def get_tesseract_service() -> TesseractService:
    return TesseractService()



@lru_cache
def get_gemini_service() -> GeminiService:
    return GeminiService(
        GeminiClient(
            settings.gemini_api_key, 
            model=settings.gemini_model
        ),
        settings.gemini_max_upload_bytes,
        settings.max_markdown_bytes,
    )


@lru_cache
def get_pdf_extraction_service() -> PdfExtractionService:
    return PdfExtractionService(get_pdf_to_markdown_service(), get_gemini_service())


@lru_cache
def get_groq_service() -> GroqService:
    client = GroqClient(settings.groq_api_key, settings.groq_model)
    return GroqService(client, settings.groq_max_upload_bytes)



def uploaded_pdf(file: UploadFile = File(...)) -> Iterator[Path]:
    """Save the upload to a temp file and yield its path; the file is deleted afterwards."""
    filename = file.filename or "upload"
    stem = re.sub(r"[^A-Za-z0-9_-]", "_", Path(filename).stem) or "upload"
    suffix = Path(filename).suffix.lower()

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"{stem}{suffix}"
        with path.open("wb") as out:
            shutil.copyfileobj(file.file, out)
        yield path


@lru_cache
def get_pdf_to_markdown_service() -> PdfToMarkdownService:
    return PdfToMarkdownService(settings.markdown_results_dir, settings.gemini_max_upload_bytes)