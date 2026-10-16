import logging
import threading
from datetime import datetime
from pathlib import Path

import pymupdf
import pymupdf4llm

from data_extraction_project.core.constants import MIN_MARKDOWN_CHARS, PDF_EXTS, PDF_MAGIC
from data_extraction_project.core.exceptions import (
    EmptyFileError,
    FileTooLargeError,
    InvalidPdfError,
    PdfConversionFailedError,
    PdfNoTextError,
    UnsupportedFileTypeError,
)

logger = logging.getLogger(__name__)


class PdfToMarkdownService:
    def __init__(self, results_dir: Path, max_upload_bytes: int) -> None:
        self._results_dir = results_dir
        self._results_dir.mkdir(parents=True, exist_ok=True)
        self._max_upload_bytes = max_upload_bytes
        # PyMuPDF is not thread-safe, so run one conversion at a time.
        self._lock = threading.Lock()

    def convert(self, pdf_path: Path) -> str:
        """Convert the PDF at `pdf_path` to Markdown, save it, and return it."""
        self._validate(pdf_path)
        markdown = self._to_markdown(pdf_path)

        if len(markdown.strip()) < MIN_MARKDOWN_CHARS:
            logger.warning("No text extracted from %s (scanned or image-only?)", pdf_path.name)
            raise PdfNoTextError()

        self._save(pdf_path, markdown)
        return markdown

    def _validate(self, pdf_path: Path) -> None:
        suffix = pdf_path.suffix.lower()
        if suffix not in PDF_EXTS:
            raise UnsupportedFileTypeError(
                suffix=suffix or "(none)", allowed=", ".join(sorted(PDF_EXTS))
            )

        size = pdf_path.stat().st_size
        if size == 0:
            raise EmptyFileError()
        if size > self._max_upload_bytes:
            raise FileTooLargeError(max_mb=f"{self._max_upload_bytes / 1_048_576:g}")

        with pdf_path.open("rb") as f:
            if f.read(len(PDF_MAGIC)) != PDF_MAGIC:
                raise InvalidPdfError()

    def _to_markdown(self, pdf_path: Path) -> str:
        try:
            with self._lock, pymupdf.open(pdf_path) as doc:
                return pymupdf4llm.to_markdown(doc, show_progress=False)
        except pymupdf.FileDataError as exc:
            logger.warning("Corrupt PDF %s: %s", pdf_path.name, exc)
            raise InvalidPdfError() from exc
        except Exception as exc:
            logger.exception("PDF conversion failed for %s", pdf_path.name)
            raise PdfConversionFailedError() from exc

    def _save(self, pdf_path: Path, markdown: str) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = self._results_dir / f"{pdf_path.stem}_{timestamp}.md"
        out_path.write_text(markdown, encoding="utf-8")