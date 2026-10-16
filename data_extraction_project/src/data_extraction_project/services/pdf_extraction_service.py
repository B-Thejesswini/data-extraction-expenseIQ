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
        """Set up the pipeline with the two services it chains together.

        Args:
            pdf_service: Converts a PDF to Markdown and saves a copy to disk.
            gemini_service: Extracts structured receipt data from text.
        """
        self._pdf_service = pdf_service
        self._gemini_service = gemini_service

    async def extract(self, pdf_path: Path) -> ExtractionResponse:
        """Extract receipt data from a PDF: PDF to Markdown, then Markdown to Gemini.

        Conversion runs in a worker thread because it is blocking and CPU-bound. The
        Markdown is passed to Gemini in memory, but `PdfToMarkdownService` also saves
        a copy to its output folder, even if the Gemini step later fails. Scanned or
        image-only PDFs fail at the conversion step, before any Gemini call is made.

        Args:
            pdf_path: Path to the PDF on disk. The caller owns the file and its cleanup.

        Returns:
            The model name, Gemini call latency in seconds (excluding PDF conversion),
            and the extracted receipt data.

        Raises:
            UnsupportedFileTypeError: The file is not a `.pdf`.
            EmptyFileError: The file has no content.
            FileTooLargeError: The PDF exceeds the upload limit, or the converted text
                exceeds the text limit.
            InvalidPdfError: The file is not a valid or readable PDF.
            PdfNoTextError: No text could be extracted (scanned or image-only PDF).
            PdfConversionFailedError: Conversion failed unexpectedly.
            ExtractionUnavailableError: Gemini is temporarily overloaded or unavailable.
            ExtractionFailedError: Gemini failed or returned unparseable output.
        """
        # Conversion is sync and CPU-bound, so keep it off the event loop.
        markdown = await asyncio.to_thread(self._pdf_service.convert, pdf_path)
        return await self._gemini_service.extract_from_text(markdown)