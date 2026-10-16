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
        self._client = client
        self._max_upload_bytes = max_upload_bytes
        self._max_text_bytes = max_text_bytes

    async def extract(self, filename: str, content: bytes) -> ExtractionResponse:
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
        text = self._validate_markdown(filename, content)
        return await self.extract_from_text(text)

    async def extract_from_text(self, text: str) -> ExtractionResponse:
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