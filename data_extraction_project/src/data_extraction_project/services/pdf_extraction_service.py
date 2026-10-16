import asyncio
from pathlib import Path

from data_extraction_project.schemas.vlm_extraction_schema import ExtractionResponse
from data_extraction_project.services.gemini_service import GeminiService
from data_extraction_project.services.pdf_markdown_service import PdfToMarkdownService


class PdfExtractionService:
    """PDF -> markdown -> Gemini -> structured receipt data."""

    def __init__(
        self, pdf_service: PdfToMarkdownService, gemini_service: GeminiService
    ) -> None:
        self._pdf_service = pdf_service
        self._gemini_service = gemini_service

    async def extract(self, pdf_path: Path) -> ExtractionResponse:
        # Conversion is sync and CPU-bound, so keep it off the event loop.
        markdown = await asyncio.to_thread(self._pdf_service.convert, pdf_path)
        return await self._gemini_service.extract_from_text(markdown)