from functools import lru_cache

from data_extraction_project.llm.providers.gemini_client import GeminiClient
from data_extraction_project.core.config import settings
from data_extraction_project.services.gemini_service import GeminiService

from data_extraction_project.services.paddleocr_service import PaddleOCRService
from data_extraction_project.services.tesseract_service import TesseractService

from data_extraction_project.llm.providers.groq_client import GroqClient
from data_extraction_project.services.groq_service import GroqService


@lru_cache
def get_ocr_service() -> PaddleOCRService:
    return PaddleOCRService()


@lru_cache
def get_tesseract_service() -> TesseractService:
    return TesseractService()


@lru_cache
def get_gemini_service() -> GeminiService:
    client = GeminiClient(settings.gemini_api_key, settings.gemini_model)
    return GeminiService(client, settings.gemini_max_upload_bytes)


@lru_cache
def get_groq_service() -> GroqService:
    client = GroqClient(settings.groq_api_key, settings.groq_model)
    return GroqService(client, settings.groq_max_upload_bytes)