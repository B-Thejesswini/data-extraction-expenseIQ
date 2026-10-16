import time
from pathlib import Path

from data_extraction_project.llm.providers.gemini_client import GeminiClient
from data_extraction_project.core.constants import GEMINI_IMAGE_MIME_TYPES, MARKDOWN_EXTS
from data_extraction_project.core.exceptions import (
    EmptyFileError,
    FileTooLargeError,
    UnsupportedFileTypeError,
    InvalidTextFileError,
)
from data_extraction_project.schemas.vlm_extraction_schema import ExtractionResponse


class GeminiService:
    def __init__(self, client: GeminiClient, max_upload_bytes: int, max_text_bytes: int) -> None:
        """Set up the service with its Gemini client and size limits.

        Args:
            client: Gemini client used for all extraction calls.
            max_upload_bytes: Largest uploaded file (image or markdown) accepted, in bytes.
            max_text_bytes: Largest text payload sent to Gemini, in bytes. Applies to
                uploaded markdown and to markdown converted from a PDF.
        """
        self._client = client
        self._max_upload_bytes = max_upload_bytes
        self._max_text_bytes = max_text_bytes

    async def extract(self, filename: str, content: bytes) -> ExtractionResponse:
        """Extract receipt data from an uploaded image.

    Validates the file type and size, sends the image to Gemini, and returns the
    structured result. `latency_s` measures the Gemini call only.

    Args:
        filename: Original upload name, used to determine the image type.
        content: Raw image bytes.

    Returns:
        The model name, Gemini call latency in seconds, and the extracted receipt data.

    Raises:
        UnsupportedFileTypeError: Extension is not a Gemini-supported image format.
        EmptyFileError: The file has no content.
        FileTooLargeError: The file exceeds `max_upload_bytes`.
        ExtractionUnavailableError: Gemini is temporarily overloaded or unavailable.
        ExtractionFailedError: Gemini failed or returned unparseable output.
    """
        mime_type = self._validate(filename, content)

        start = time.perf_counter()
        data = await self._client.extract_receipt(content, mime_type)
        latency = time.perf_counter() - start

        return ExtractionResponse(
            model=self._client.model,
            latency_s=round(latency, 3),
            data=data,
        )

    async def extract_markdown(self, filename: str, content: bytes) -> ExtractionResponse:
        """Extract receipt data from an uploaded markdown file.

    Validates and decodes the upload, then delegates to `extract_from_text`.

    Args:
        filename: Original upload name, used to check for a markdown extension.
        content: Raw bytes of the markdown file.

    Returns:
        The model name, Gemini call latency in seconds, and the extracted receipt data.

    Raises:
        UnsupportedFileTypeError: Extension is not `.md` or `.markdown`.
        EmptyFileError: The file is empty or contains only whitespace.
        FileTooLargeError: The file or its text exceeds the size limits.
        InvalidTextFileError: The file is not valid UTF-8.
        ExtractionUnavailableError: Gemini is temporarily overloaded or unavailable.
        ExtractionFailedError: Gemini failed or returned unparseable output.
    """
        text = self._validate_markdown(filename, content)
        return await self.extract_from_text(text)

    async def extract_from_text(self, text: str) -> ExtractionResponse:
        """Extract receipt data from text that is already in memory.

    Shared by the markdown upload route and the PDF pipeline. Enforces the text
    size cap before calling Gemini, so oversized input costs no API call.

    Args:
        text: Markdown or plain text of the receipt.

    Returns:
        The model name, Gemini call latency in seconds, and the extracted receipt data.

    Raises:
        FileTooLargeError: The text exceeds `max_text_bytes`.
        ExtractionUnavailableError: Gemini is temporarily overloaded or unavailable.
        ExtractionFailedError: Gemini failed or returned unparseable output.
    """
        if len(text.encode("utf-8")) > self._max_text_bytes:
            raise FileTooLargeError(max_mb=self._max_text_bytes // (1024 * 1024))

        start = time.perf_counter()
        data = await self._client.extract_receipt_from_text(text)
        latency = time.perf_counter() - start

        return ExtractionResponse(
            model=self._client.model,
            latency_s=round(latency, 3),
            data=data,
        )


    def _validate(self, filename: str, content: bytes) -> str:
        """Validate an uploaded image and return its MIME type.

    The MIME type is derived from the file extension, not from the client-supplied
    content type, since the client controls the latter.

    Raises:
        UnsupportedFileTypeError: Extension is not a Gemini-supported image format.
        EmptyFileError: The file has no content.
        FileTooLargeError: The file exceeds `max_upload_bytes`.
    """

        suffix = Path(filename).suffix.lower()
        mime_type = GEMINI_IMAGE_MIME_TYPES.get(suffix)
        if mime_type is None:
            raise UnsupportedFileTypeError(
                suffix=suffix or "(none)",
                allowed=", ".join(sorted(GEMINI_IMAGE_MIME_TYPES)),
            )
        if not content:
            raise EmptyFileError()
        if len(content) > self._max_upload_bytes:
            raise FileTooLargeError(max_mb=self._max_upload_bytes // (1024 * 1024))
        return mime_type


    def _validate_markdown(self, filename: str, content: bytes) -> str:
        """Validate an uploaded markdown file and return its decoded text.

    Decodes as UTF-8 and strips a leading BOM if present.

    Raises:
        UnsupportedFileTypeError: Extension is not `.md` or `.markdown`.
        EmptyFileError: The file is empty or contains only whitespace.
        FileTooLargeError: The file exceeds `max_upload_bytes`.
        InvalidTextFileError: The file is not valid UTF-8.
    """
        suffix = Path(filename).suffix.lower()
        if suffix not in MARKDOWN_EXTS:
            raise UnsupportedFileTypeError(
                suffix=suffix or "(none)",
                allowed=", ".join(sorted(MARKDOWN_EXTS)),
            )
        if not content:
            raise EmptyFileError()
        if len(content) > self._max_upload_bytes:
            raise FileTooLargeError(max_mb=self._max_upload_bytes // (1024 * 1024))
        try:
            text = content.decode("utf-8-sig")  # also strips a BOM if present
        except UnicodeDecodeError as exc:
            raise InvalidTextFileError() from exc
        if not text.strip():
            raise EmptyFileError()
        return text