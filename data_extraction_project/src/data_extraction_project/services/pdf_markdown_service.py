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
        """Create the output folder and set up the converter.

        Args:
            results_dir: Folder where converted Markdown files are saved. Created if it
                does not exist.
            max_upload_bytes: Largest PDF accepted, in bytes.
        """
        self._results_dir = results_dir
        self._results_dir.mkdir(parents=True, exist_ok=True)
        self._max_upload_bytes = max_upload_bytes
        # PyMuPDF is not thread-safe, so run one conversion at a time.
        self._lock = threading.Lock()

    def convert(self, pdf_path: Path) -> str:
        """Convert the PDF at `pdf_path` to Markdown, save a copy, and return it.

    Blocking and CPU-bound, so call it from a worker thread rather than directly on
    the event loop. PyMuPDF is not thread-safe, so conversions are serialized with a
    lock and run one at a time. The copy is saved to `results_dir` as
    `<name>_<timestamp>.md`, and only after the text check passes, so nothing is
    saved for scanned PDFs.

    Args:
        pdf_path: Path to the PDF on disk. The caller owns the file and its cleanup.

    Returns:
        The Markdown text of the whole document.

    Raises:
        UnsupportedFileTypeError: The file is not a `.pdf`.
        EmptyFileError: The file has no content.
        FileTooLargeError: The file exceeds `max_upload_bytes`.
        InvalidPdfError: The file is not a valid or readable PDF.
        PdfNoTextError: Almost no text was extracted, so the PDF is probably scanned
            or image-only and would need OCR.
        PdfConversionFailedError: Conversion failed unexpectedly.
    """
        self._validate(pdf_path)
        markdown = self._to_markdown(pdf_path)

        if len(markdown.strip()) < MIN_MARKDOWN_CHARS:
            logger.warning("No text extracted from %s (scanned or image-only?)", pdf_path.name)
            raise PdfNoTextError()

        self._save(pdf_path, markdown)
        return markdown

    def _validate(self, pdf_path: Path) -> None:
        """Check that the file is a non-empty, size-limited PDF.

        Checks the extension, then the size, then the leading `%PDF-` bytes. The magic
        bytes catch files renamed to `.pdf`, but a file that passes can still be corrupt,
        which is caught later during conversion.

        Raises:
            UnsupportedFileTypeError: The file is not a `.pdf`.
            EmptyFileError: The file has no content.
            FileTooLargeError: The file exceeds `max_upload_bytes`.
            InvalidPdfError: The file does not start with the PDF header.
        """


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
        """Run PyMuPDF on the PDF and return the Markdown text.

        The lock is held for the whole conversion. Details of failures are logged and
        never exposed to the caller.

        Raises:
            InvalidPdfError: PyMuPDF could not read the file data (corrupt PDF).
            PdfConversionFailedError: Any other conversion failure.
        """
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
        """Write the Markdown to `results_dir` as `<name>_<timestamp>.md`.

        The timestamp keeps repeated conversions of the same file from overwriting each
        other. The name comes from the PDF's stem, so callers should pass sanitized names.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = self._results_dir / f"{pdf_path.stem}_{timestamp}.md"
        out_path.write_text(markdown, encoding="utf-8")